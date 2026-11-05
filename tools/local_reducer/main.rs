//! Install the rendered r-sure contracts into the node's own in-memory reducer and call
//! a few public arms. No devnet, no Docker, no network.
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
            sender: PublicKey::new(ADMINS[0].as_bytes().to_vec()),
            seq_num: SeqNum::zero(),
            timestamp: 0,
        });
        Ok(Self { runtime, deploy: 0 })
    }

    /// Evaluate one term as a deploy and return the pretty-printed reply data.
    async fn deploy(&mut self, term: &str) -> Result<Vec<String>, Error> {
        self.deploy += 1;
        let id = vec![self.deploy as u8; 64];
        let mut env = BTreeMap::new();
        env.insert(
            "rho:rchain:deployerId".to_string(),
            RhoDeployerId::apply(ADMINS[0].as_bytes().to_vec()),
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

    let stub = r#"new rs(`rho:registry:insertArbitrary`), resolverCh, rootCh, ack,
    deployId(`rho:rchain:deployId`), Resolver, Root,
    Issuer, Purse in {
  contract Resolver(@"issuer", @assetId, ret) = { ret!((true, "REV-brand", *Issuer)) } |
  contract Issuer(@"makeEmptyPurse", ret) = { ret!((true, *Purse)) } |
  contract Purse(@"deposit", @payment, ret) = { ret!((true, 0)) } |
  contract Purse(@"getAmountOf", @payment, ret) = { ret!((true, 0)) } |
  contract Purse(@"withdraw", @spec, ret) = { ret!((false, "stub purse")) } |
  rs!(bundle+{*Resolver}, *resolverCh) |
  for (@resolverUri <- resolverCh) {
    contract Root(@"resolve", @key, @minVersion, ret) = {
      if (key == "component:asset-resolver") { ret!((true, resolverUri, 1)) }
      else { ret!((false, "unknown", key)) }
    } |
    rs!(bundle+{*Root}, *rootCh) |
    for (@uri <- rootCh) { deployId!([uri]) }
  }
}"#;
    let rcash = reducer
        .deploy(stub)
        .await?
        .join(" ");
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
