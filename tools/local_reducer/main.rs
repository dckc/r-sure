//! Install the built r-sure contracts into the node's own in-memory reducer and drive a
//! placement from syndicate creation through claim settlement. No devnet, no Docker, no
//! network.
//!
//! `tools/local_reducer.sh` generates a crate around this file, pointing it at the
//! RNodeRust checkout, and runs it. The point is to catch install-time and call-time
//! failures (free variables, sort errors, deadlock shapes) before any block is proposed.
//!
//! The reducer is the node's `RhoRuntime`, so the semantics are the node's. It is not a
//! substitute for the devnet campaign: r-cash, r-gen and finality are absent.

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use rchain_crypto::hash::blake2b512_random::Blake2b512Random;
use rchain_crypto::public_key::PublicKey;
use rchain_models::rholang::RhoType::{RhoDeployId, RhoDeployerId};
use rchain_models::runtime::{BindPattern, ListParWithRandom, TaggedContinuation};
use rchain_models::sorted::SortedProc;
use rchain_rholang::pretty_printer::PrettyPrinter;
use rchain_rholang::runtime::RhoRuntime;
use rchain_rholang::storage::RhoMatch;
use rchain_rholang::system_processes::BlockData;
use rchain_rspace::factory::create_history_repository;
use rchain_rspace::hot_store::InMemHotStore;
use rchain_rspace::rspace::RSpace;
use rchain_shared::refined::{BlockHeight, SeqNum};
use rchain_shared::store_manager::InMemoryStoreManager;

const ORDER: &[&str] = &[
    "00_root.rho",
    "01_kernel.rho",
    "02_admin.rho",
    "03_terms.rho",
    "04_math.rho",
    "05_rgen.rho",
    "40_payments.rho",
    "15_distribution.rho",
    "16_fund.rho",
    "10_syndicate.rho",
    "11_broker.rho",
    "12_risk.rho",
    "13_slip.rho",
    "14_line.rho",
    "17_policy.rho",
    "18_claim.rho",
    "19_books.rho",
];

// Valid 65-byte secp256k1 public keys. They are identities only: the local reducer never
// signs anything, and no secret is involved.
const ADMINS: [&str; 3] = [
    "04df0092d2416c46f9e8711136f90f3c9026ed3ccf8c82ffff944e6a1215e53cc9d361ef70ab28417ebd979a92411397d5abf00ef7657029a9674e9875cb5739c2",
    "04db11c81588f16118564d383d9f7d6ee86318d1c0d04a3bcfbb315d4110f25c7056f6c0369fc66c985d94deb9d89ed4b6e99686eb47425352eba9c50dc3368fe2",
    "04ff68fdfc50f6ca6b71f8b0e390f756375be510e5145402cb212df23468500f3315e3667ef871bf6e8902c6ea2edd25942d17593a66f9ee3c9a451d7de3585812",
];
const PLATFORM: &str = "11112VYAt8rUGNRRZX3eJdgagaAhtWTK8Js7F7X5iqddMVqyDTtYau";

fn deployer_key() -> Vec<u8> {
    fn nibble(ch: char) -> u8 {
        match ch {
            '0'..='9' => ch as u8 - b'0',
            'a'..='f' => ch as u8 - b'a' + 10,
            'A'..='F' => ch as u8 - b'A' + 10,
            _ => 0,
        }
    }
    let hex = ADMINS[0].as_bytes();
    hex.chunks(2)
        .map(|pair| (nibble(pair[0] as char) << 4) | nibble(pair[1] as char))
        .collect()
}

type Error = Box<dyn std::error::Error>;

struct Reducer {
    runtime: RhoRuntime,
    deploy: usize,
}

impl Reducer {
    async fn new() -> Result<Self, Error> {
        let manager = InMemoryStoreManager::default();
        let history = create_history_repository::<
            SortedProc,
            BindPattern,
            ListParWithRandom,
            TaggedContinuation,
        >(&manager, "rspace")
        .await?;
        let reader = history.get_history_reader(history.root()).await;
        let hot = Arc::new(InMemHotStore::new(reader.base()));
        let (play, _replay) = RSpace::create_with_replay(history.clone(), hot, Arc::new(RhoMatch));
        let runtime = RhoRuntime::create(play, history, SortedProc::default()).await?;
        runtime.set_block_data(BlockData {
            block_number: BlockHeight::zero(),
            sender: PublicKey::new(deployer_key()),
            seq_num: SeqNum::zero(),
            timestamp: 0,
        });
        Ok(Self { runtime, deploy: 0 })
    }

    /// Resolve a component key through the root and call one arm.
    async fn component_call(
        &mut self,
        root: &str,
        key: &str,
        arm: &str,
        args: &str,
    ) -> Result<String, Error> {
        let term = format!(
            "new rl(`rho:registry:lookup`), rootCh, resolveCh, capCh, reply, \
             dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{ \
             rl!(`{root}`, *rootCh) | \
             for (Root <- rootCh) {{ Root!(\"resolve\", \"{key}\", 1, *resolveCh) }} | \
             for (@(true, uri, _) <- resolveCh) {{ \
               rl!(uri, *capCh) | for (Cap <- capCh) {{ Cap!(\"{arm}\"{args}, *reply) }} }} | \
             for (@r <- reply) {{ deployId!(r) }} }}"
        );
        Ok(self.deploy(&term).await?.join(" "))
    }

    /// Call one arm on a known URI.
    async fn uri_call(&mut self, uri: &str, arm: &str, args: &str) -> Result<String, Error> {
        let term = format!(
            "new rl(`rho:registry:lookup`), capCh, reply, \
             dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{ \
             rl!(`{uri}`, *capCh) | \
             for (Cap <- capCh) {{ Cap!(\"{arm}\"{args}, *reply) }} | \
             for (@r <- reply) {{ deployId!(r) }} }}"
        );
        Ok(self.deploy(&term).await?.join(" "))
    }

    /// Evaluate one term as a deploy and return the pretty-printed reply data.
    async fn deploy(&mut self, term: &str) -> Result<Vec<String>, Error> {
        self.deploy += 1;
        let id = vec![self.deploy as u8; 64];
        let mut env = BTreeMap::new();
        env.insert(
            "rho:rchain:deployerId".to_string(),
            RhoDeployerId::apply(deployer_key()),
        );
        env.insert(
            "rho:rchain:deployId".to_string(),
            RhoDeployId::apply(id.clone()),
        );
        let rand = Blake2b512Random::new_random(128);
        let result = self.runtime.evaluate_with_env(term, &env, &rand).await?;
        if !result.errors.is_empty() {
            return Err(std::io::Error::other(format!(
                "deploy {} reduced with errors: {:?}",
                self.deploy, result.errors
            ))
            .into());
        }
        let channel = SortedProc::new(RhoDeployId::apply(id));
        let data = self.runtime.get_data_par(&channel).await?;
        let printer = PrettyPrinter::new();
        Ok(data.iter().map(|par| printer.build_string(par)).collect())
    }
}

fn render(source: &str, root: &str, rcash: &str) -> String {
    let admins = format!(
        "[{}]",
        ADMINS
            .iter()
            .map(|key| format!("\"{key}\".hexToBytes()"))
            .collect::<Vec<_>>()
            .join(", ")
    );
    [
        ("__ADMINS__", admins.as_str()),
        ("__THRESHOLD__", "2"),
        ("__ROOT_URI__", root),
        ("__RCASH_ROOT_URI__", rcash),
        ("__PLATFORM_OWNER__", PLATFORM),
        ("__RGEN_ROOT_URI__", ""),
    ]
    .into_iter()
    .fold(source.to_string(), |text, (key, value)| {
        text.replace(key, value)
    })
}

fn first_quoted(text: &str) -> Option<String> {
    let start = text.find('"')? + 1;
    let rest = &text[start..];
    let end = rest.find('"')?;
    Some(rest[..end].to_string())
}

fn find_uri(text: &str) -> Option<String> {
    let start = text.find("rho:id:")?;
    let rest = &text[start..];
    let end = rest
        .char_indices()
        .find(|(_, ch)| !(ch.is_ascii_alphanumeric() || *ch == ':'))
        .map(|(index, _)| index)
        .unwrap_or(rest.len());
    Some(rest[..end].to_string())
}

fn build_dir() -> Result<PathBuf, Error> {
    let dir = std::env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| Path::new("contracts/build").to_path_buf());
    if !dir.is_dir() {
        return Err(std::io::Error::other(format!(
            "{} is missing; run `make build` first",
            dir.display()
        ))
        .into());
    }
    Ok(dir)
}

async fn run() -> Result<(), Error> {
    let build = build_dir()?;
    let mut reducer = Reducer::new().await?;

    let stub = r#"new rs(`rho:registry:insertArbitrary`), resolverCh, factoryCh, rootCh,
    deployId(`rho:rchain:deployId`), Resolver, AccountFactory, Account, Facet, Root,
    Issuer, Purse in {
  contract Resolver(@"issuer", @assetId, ret) = { ret!((true, "REV-brand", *Issuer)) } |
  contract Issuer(@"makeEmptyPurse", ret) = { ret!((true, *Purse)) } |
  contract Issuer(@"getAmountOf", @payment, ret) = { match payment { "premium:1000" => { ret!((true, 1000)) } "stub-payment" => { ret!((true, 6000)) } amount => { ret!((true, amount)) } } } |
  contract Purse(@"deposit", @payment, ret) = { ret!((true, 0)) } |
  contract Purse(@"getAmountOf", @payment, ret) = { ret!((true, 6000)) } |
  contract Purse(@"getCurrentAmount", ret) = { ret!((true, 6000)) } |
  contract Purse(@"withdraw", @spec, ret) = { match spec { (brand, amount) => { ret!((true, amount)) } } } |
  contract AccountFactory(@"accountOf", @owner, ret) = { ret!((true, *Account)) } |
  contract AccountFactory(@"getOrCreate", @pk, ret) = { ret!((true, *Account, "stub-owner")) } |
  contract Account(@"depositFacet", @assetId, ret) = { ret!((true, *Facet)) } |
  contract Account(@"deposit", @payment, ret) = { ret!((true, 0)) } |
  contract Facet(@"deposit", @payment, ret) = { ret!((true, 0)) } |
  rs!(bundle+{*Resolver}, *resolverCh) |
  rs!(bundle+{*AccountFactory}, *factoryCh) |
  for (@resolverUri <- resolverCh; @factoryUri <- factoryCh) {
    contract Root(@"resolve", @key, @minVersion, ret) = {
      if (key == "component:asset-resolver") { ret!((true, resolverUri, 1)) }
      else {
        if (key == "component:account-factory") { ret!((true, factoryUri, 1)) }
        else { ret!((false, "unknown", key)) }
      }
    } |
    rs!(bundle+{*Root}, *rootCh) |
    for (@uri <- rootCh) { deployId!([uri]) }
  }
}"#;
    let rcash = reducer.deploy(stub).await?.join(" ");
    let rcash = find_uri(&rcash)
        .ok_or_else(|| std::io::Error::other(format!("rcash stub: no URI in {rcash}")))?;
    println!("local-reducer: r-cash stub {rcash}");

    let mut root = String::new();
    for name in ORDER {
        let source = std::fs::read_to_string(build.join(name))?;
        let term = render(&source, &root, &rcash);
        let replies = reducer.deploy(&term).await?;
        let joined = replies.join(" ");
        if name == &"00_root.rho" {
            root = find_uri(&joined).ok_or_else(|| {
                std::io::Error::other(format!("00_root.rho: no root URI in {joined}"))
            })?;
            println!("local-reducer: root {root}");
        } else if replies.is_empty() {
            return Err(std::io::Error::other(format!("{name}: no reply")).into());
        } else {
            println!("local-reducer: installed {name}");
        }
    }

    let resolve = format!(
        "new rl(`rho:registry:lookup`), rootCh, reply, deployId(`rho:rchain:deployId`) in {{ \
         rl!(`{root}`, *rootCh) | \
         for (Root <- rootCh) {{ Root!(\"resolve\", \"component:clock\", 1, *reply) }} | \
         for (@r <- reply) {{ deployId!(r) }} }}"
    );
    let clock = reducer.deploy(&resolve).await?.join(" ");
    if !clock.contains("true") || !clock.contains("rho:id:") {
        return Err(std::io::Error::other(format!("resolve clock: {clock}")).into());
    }
    println!("local-reducer: resolve component:clock -> {clock}");

    let keys = format!(
        "new rl(`rho:registry:lookup`), rootCh, reply, deployId(`rho:rchain:deployId`) in {{ \
         rl!(`{root}`, *rootCh) | \
         for (Root <- rootCh) {{ Root!(\"keys\", *reply) }} | \
         for (@r <- reply) {{ deployId!(r) }} }}"
    );

    let math = format!(
        "new rl(`rho:registry:lookup`), rootCh, resolveCh, capCh, mathCh, \
         deployId(`rho:rchain:deployId`) in {{ \
         rl!(`{root}`, *rootCh) | \
         for (Root <- rootCh) {{ Root!(\"resolve\", \"component:suremath\", 1, *resolveCh) }} | \
         for (@(true, uri, _) <- resolveCh) {{ \
           rl!(uri, *capCh) | \
           for (SureMath <- capCh) {{ SureMath!(\"share\", 1000, 250, *mathCh) }} }} | \
         for (@m <- mathCh) {{ deployId!(m) }} }}"
    );
    let share = reducer.deploy(&math).await?.join(" ");
    if !share.contains("true") || !share.contains("25") || !share.contains("975") {
        return Err(std::io::Error::other(format!("suremath share: {share}")).into());
    }
    println!("local-reducer: suremath share(1000, 250) -> {share}");

    let address = reducer
        .deploy(
            "new dops(`rho:rchain:deployerId:ops`), rev(`rho:rev:address`), \
             dId(`rho:rchain:deployerId`), pkCh, addrCh, \
             deployId(`rho:rchain:deployId`) in { \
             dops!(\"pubKeyBytes\", *dId, *pkCh) | \
             for (@pk <- pkCh) { rev!(\"fromPublicKey\", pk, *addrCh) } | \
             for (@a <- addrCh) { deployId!(a) } }",
        )
        .await?
        .join(" ");
    let insured = first_quoted(&address)
        .ok_or_else(|| std::io::Error::other(format!("insured address: {address}")))?;
    println!("local-reducer: insured {insured}");

    let syndicate_args =
        r#", *dId, {"name": "local-syndicate", "assetId": "REV", "riskAppetite": ["property"]}"#;
    let syndicate = reducer
        .component_call(&root, "component:syndicate-book", "create", syndicate_args)
        .await?;
    let syndicate_id = first_quoted(&syndicate)
        .ok_or_else(|| std::io::Error::other(format!("syndicate create: {syndicate}")))?;
    let syndicate_uri = find_uri(&syndicate)
        .ok_or_else(|| std::io::Error::other(format!("syndicate create: {syndicate}")))?;
    println!("local-reducer: syndicate {syndicate_id} {syndicate_uri}");

    let contributed = reducer
        .uri_call(&syndicate_uri, "contribute", r#", *dId, "stub-payment""#)
        .await?;
    if !contributed.contains("true") {
        return Err(std::io::Error::other(format!("contribute: {contributed}")).into());
    }
    println!("local-reducer: contributed {contributed}");

    let broker_args = r#", *dId, {"name": "local-broker", "licenceHash": "licence:local", "commissionBps": 1000, "classes": ["property"]}"#;
    let broker = reducer
        .component_call(&root, "component:broker-book", "register", broker_args)
        .await?;
    if !broker.contains("true") || !broker.contains("rho:id:") {
        return Err(std::io::Error::other(format!("broker register: {broker}")).into());
    }
    println!("local-reducer: broker {broker}");

    let risk_args = r#", *dId, {"class": "property", "assetRef": {"kind": "site", "hash": "asset:local"}, "evidence": [{"kind": "loss-run", "hash": "loss:local"}], "triTest": {"exposureRef": "exposure:local", "probabilityBasis": "claims-history", "consequenceBasis": "declared-value", "consequenceRef": "consequence:local"}, "periodStart": 0, "periodEnd": 1000000, "declaredValue": 5000, "requestedLimit": 1000, "requestedDeductible": 0}"#;
    let risk = reducer
        .component_call(&root, "component:risk-book", "submit", risk_args)
        .await?;
    let risk_id =
        first_quoted(&risk).ok_or_else(|| std::io::Error::other(format!("risk submit: {risk}")))?;
    let risk_uri =
        find_uri(&risk).ok_or_else(|| std::io::Error::other(format!("risk submit: {risk}")))?;
    println!("local-reducer: risk {risk_id} {risk_uri}");

    let terms = r#"{"coverageClass": "property", "assetId": "REV", "aggregateLimit": 5000, "perClaimLimit": 1000, "deductible": 0, "premiumTotal": 1000, "periodStartHeight": 0, "periodEndHeight": 1000000, "waitingBlocks": 0, "noticeBlocks": 1000, "runOffBlocks": 100, "standardClaimMax": 1000, "minSyndicates": 1, "maxSyndicates": 1, "brokerCommissionBps": 1000, "centralFundBps": 250, "evidencePolicy": "optional", "claimsLeadPolicy": "lead"}"#;
    let mut slip_args = String::from(", *dId, {\"riskId\": ");
    slip_args.push_str(&format!("{risk_id:?}, \"riskUri\": {risk_uri:?}, \"insured\": {insured:?}, \"class\": \"property\", \"terms\": "));
    slip_args.push_str(terms);
    slip_args.push_str(", \"expiryHeight\": 1000000}");
    let slip = reducer
        .component_call(&root, "component:slip-factory", "open", &slip_args)
        .await?;
    if !slip.contains("true") || !slip.contains("rho:id:") {
        return Err(std::io::Error::other(format!("slip open: {slip}")).into());
    }
    println!("local-reducer: slip {slip}");

    let slip_id =
        first_quoted(&slip).ok_or_else(|| std::io::Error::other(format!("slip open: {slip}")))?;
    let slip_uri =
        find_uri(&slip).ok_or_else(|| std::io::Error::other(format!("slip open: {slip}")))?;

    let subscribe_args = format!(r#", *dId, "{syndicate_uri}", 10000"#);
    let subscribed = reducer
        .uri_call(&slip_uri, "subscribe", &subscribe_args)
        .await?;
    if !subscribed.contains("true") {
        return Err(std::io::Error::other(format!("subscribe: {subscribed}")).into());
    }
    println!("local-reducer: subscribed {subscribed}");

    let accepted = reducer.uri_call(&slip_uri, "accept", ", *dId").await?;
    if !accepted.contains("true") {
        return Err(std::io::Error::other(format!("accept: {accepted}")).into());
    }
    println!("local-reducer: accepted {accepted}");

    let funded = reducer
        .uri_call(&slip_uri, "fundPremium", r#", *dId, "premium:1000""#)
        .await?;
    if !funded.contains("true") {
        return Err(std::io::Error::other(format!("fundPremium: {funded}")).into());
    }
    println!("local-reducer: funded {funded}");

    let bind = reducer.uri_call(&slip_uri, "bind", "").await?;
    if !bind.contains("true") || !bind.contains("rho:id:") {
        let slip_info = reducer.uri_call(&slip_uri, "info", "").await?;
        let quotes = reducer.uri_call(&syndicate_uri, "quotes", "").await?;
        let lines = reducer.uri_call(&syndicate_uri, "lines", "").await?;
        return Err(std::io::Error::other(format!(
            "bind: {bind}\n  slip: {slip_info}\n  quotes: {quotes}\n  lines: {lines}"
        ))
        .into());
    }
    println!("local-reducer: bound {slip_id} -> {bind}");

    let policy_uri =
        find_uri(&bind).ok_or_else(|| std::io::Error::other(format!("bind: {bind}")))?;
    let claim_req = r#", *dId, {"lossHeight": 0, "claimedAmount": 800, "evidence": [{"kind": "loss", "hash": "loss:local"}]}"#;
    let claim = reducer
        .uri_call(&policy_uri, "openClaim", claim_req)
        .await?;
    let claim_id =
        first_quoted(&claim).ok_or_else(|| std::io::Error::other(format!("openClaim: {claim}")))?;
    let claim_uri =
        find_uri(&claim).ok_or_else(|| std::io::Error::other(format!("openClaim: {claim}")))?;
    println!("local-reducer: claim {claim_id} {claim_uri}");

    let classified = reducer
        .uri_call(&claim_uri, "classify", r#", *dId, "standard""#)
        .await?;
    if !classified.contains("true") {
        return Err(std::io::Error::other(format!("classify: {classified}")).into());
    }
    let assessed = reducer
        .uri_call(
            &claim_uri,
            "assess",
            r#", *dId, {"recommendedAmount": 800, "basisHash": "assessment"}"#,
        )
        .await?;
    if !assessed.contains("true") {
        return Err(std::io::Error::other(format!("assess: {assessed}")).into());
    }
    let agreed = reducer
        .uri_call(&claim_uri, "agree", r#", *dId, 800, "agreement""#)
        .await?;
    if !agreed.contains("true") {
        return Err(std::io::Error::other(format!("agree: {agreed}")).into());
    }
    println!("local-reducer: claim agreed -> {agreed}");

    let settled = reducer.uri_call(&claim_uri, "settle", "").await?;
    if !settled.contains("true") {
        return Err(std::io::Error::other(format!("settle: {settled}")).into());
    }
    let closed = reducer.uri_call(&claim_uri, "close", "").await?;
    if !closed.contains("true") {
        return Err(std::io::Error::other(format!("close: {closed}")).into());
    }
    let claim_info = reducer.uri_call(&claim_uri, "info", "").await?;
    if !claim_info.contains("closed") || !claim_info.contains(r#""paid" : 800"#) {
        return Err(std::io::Error::other(format!("claim info: {claim_info}")).into());
    }
    println!("local-reducer: claim settled and closed");
    let keys = reducer.deploy(&keys).await?.join(" ");
    let registered = keys.matches("component:").count();
    if !keys.contains("true") || registered != 21 {
        return Err(std::io::Error::other(format!(
            "root keys: expected 21 components, got {registered}: {keys}"
        ))
        .into());
    }
    println!("local-reducer: root keys -> {registered} components");
    Ok(())
}

fn main() -> Result<(), Error> {
    tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()?
        .block_on(run())
}
