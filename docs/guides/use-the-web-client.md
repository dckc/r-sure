# Use the web client

> **Status:** Implemented and exercised on devnet. Devnet-only, unaudited, no real value.

The `web/` app is the transactional client for r-sure: it creates a wallet, reads the live
market books, and drives the placement, policy, claim, fund and admin flows through the
WASM client. It is not a separate server and does not hold keys: the private key lives
inside the WASM module, and the encrypted keystore is stored in the browser's IndexedDB.

## Prerequisites

- the devnet install is complete (`make devnet`, `make rcash-keys rcash-bootstrap`,
  `make keys install`);
- Node 22 and `wasm-pack` are installed;
- the `wasm32-unknown-unknown` Rust target is installed.

The default network is `http://localhost:40403`, shard `/root`, phlo price 1. Change it in
**Settings** or with `VITE_RSURE_NODE`.

## Run

```sh
make web-install
npm --prefix web run dev      # Vite dev server, http://localhost:5173
```

Production check:

```sh
make web-lint web-test web-build   # typecheck, Vitest, ESLint, Vite build
make web-e2e                       # Playwright against the installed devnet
```

`npm run build` regenerates the WASM package and copies `deployments/devnet.json` and
`deployments/catalogue.json` into `web/public/` automatically.

## Wallet

Open the wallet chip in the header. You can create a wallet or import an existing Web3 v3
keystore. Creating a wallet writes the encrypted keystore to IndexedDB; the password is
never stored. **Settings → Export keystore** downloads the encrypted document, and
**Lock** discards the in-memory key.

One wallet can play every role. Pages compare the connected address with the object's
`insured`, `brokerOwner`, `managerId` or lead/second manager and enable only the actions
that address may take. A read-only page says why.

## Discovery

There is no indexer. The client reads:

- `SyndicateBook`, `BrokerBook`, `RiskBook`, `PolicyBook` and `ClaimBook` for live lists;
- the risk's slip link and a slip's policy link;
- an optional curated catalogue in `deployments/catalogue.json`.

To populate the catalogue with real demo placements on a running devnet:

```sh
make web-seed
make web-build      # or npm run build: copies the catalogue into public/
```

The seed creates three placements (open slip, bound policy with a settled claim, and a
policy with an open claim) and writes `.demo/seed-devnet.json` with the URIs. Every
catalogue entry is a real registry URI; the app re-reads each object from the chain.

## Placement journey

The pages follow the contract lifecycle, and each step links to the next:

1. **Syndicates → Create syndicate**, then contribute capital.
2. **Brokers → Register broker** for the intermediary.
3. **Risks → Submit risk**, then assess and accept it.
4. **Open slip** from the accepted risk. The broker's address must own the risk's broker.
5. The syndicate manager **subscribes** a share; the insured **accepts**.
6. **Fund premium** withdraws the premium from the insured's r-cash account into the slip
   purse in one signed deploy.
7. **Bind** opens the lines, creates the policy and distributes the premium. Bind is
   permissionless once every precondition holds.

## Claims and the fund

A policy page opens a claim (`openClaim`) with a loss height, amount and evidence hash.
The claim page classifies, assesses, agrees, disputes, settles and closes; the lead and
second managers are the only addresses allowed to act. Settlement pays each line exactly
once and draws any shortfall from the central fund under its cap.

The **Fund** page reads the fund balance and shortfalls and contributes REV. Fund cover
and admin actions are 2-of-3 gated.

## Administration

**Admin** reads the admin set, pause state and nonce. It builds the canonical payload,
signs with saved admin profiles, and submits the 2-of-3 `SureAdmin.admin` call. Pausing is
narrow and fail-closed: it stops new placements and payouts without freezing reads.

## Boundaries

- Token-gated arms are not UI actions. Slip and policy tokens stay inside their contracts;
  `Policy.distribute` runs inside `Slip.bind`, `Line.pay` runs inside
  `Policy.settleClaim`, and `Syndicate.quote`/`openLine` run inside `Slip.subscribe`/`bind`.
- Only evidence hashes are on-chain. File upload is disabled.
- Search, fiat ramps, KYC and notifications are disabled with an honest reason; there is no
  event stream to index.
- This is a devnet client for contracts that have not been independently audited. Do not
  use it with real value.
