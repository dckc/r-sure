# r-sure operating notes

Authority order: `contracts/src` and the static gates > `docs/` > this file.

## Platform pitfalls

- **One state cell per object.** Consume first (`for (@s <- state)`), validate on the
  consumed snapshot, repost exactly once on every path. Reads peek (`<<-`) and are hints only.
- **Never store a capability in a state map.** Capabilities live in contract closures. The
  slip token, policy token and claim token are names compared with `*a != *b`; only their
  holders can spend.
- **Resolve components per arm.** Do not cache a Root-resolved capability in a bundle. The
  only stored value is the r-cash (and optional r-gen) Root URI.
- **No `select`.** The node desugars it into parallel receives. Use one consumable datum.
- **Deploy cap is 64 KiB inclusive; the hard budget is 56 KiB per term.** Measure after every
  change.
- **A deploy is atomic, blocks are sequential.** Deploys do not interleave. Repost before an
  external await where possible; after a value move, an unexpected branch calls `1/0`.
- **`*x` sends a name; `@x` sends data.** Purses, facets and tokens are names.
- **No timers.** Use block heights. Expiry is lazy and permissionless.
- **`rho:block:data` timestamp is the proposer's wall clock**, not consensus. Use the height.
- **Explore-deploy has no block context.** Anything reading the clock must be signed.
- **Deploy lifespan is 50 blocks.** Anchor `validAfterBlockNumber` at the tip.
- **Finality.** Require finalized + processedWithSuccess + `(true, …)`; never retry a
  value-moving deploy with a new op id unless the first had no effect.
- **No indexer.** Discovery is a curated catalogue plus share links. Policy/Claim books are
  on-chain indexes, not a search service.
- **r-gen is optional.** `RgenAdapter.enabled` is false by default; settlement never requires
  it. With `strictCredentials` true, a declared credential must verify.

## Commands

```
make spec-check      # build, measure, architecture, captures, select, placeholders, money, suites
make parse-check     # render and parse with the target node's parser
make docs            # build docs/book with mdBook
make docs-check      # docs links and mdBook build
make devnet          # r-cash devnet via RCASH_DIR/RHOLO_DIR
make rcash-keys      # generate and faucet the r-cash keys
make rcash-bootstrap # install the r-cash components r-sure needs
make keys install    # copy keys and install r-sure
make unit-all        # all behavioural suites (honest not-run is reported)
make formal-check    # Lean build, axioms, vectors, flows and claims register
make audit-check     # registers, arm inventory, traceability, 30 component and 42 interface coverage
make audit-scan      # heuristic bundle/take-repost/reply-shape/pause scanners (open P0s fail)
make client-lint/test/wasm
make web-test web-build
```

## Rules for changes

- Every mutating arm checks `opId`/`nonce` first and returns the prior result without a
  second effect.
- Every new arm needs a refusal test and an idempotency test.
- Every value-moving path needs a conservation assertion.
- Subscriptions sum to 10000 bps; the last line absorbs the remainder. A quote reserves
  capacity and a `LineGrant` is one-shot.
- A claim settles once. `Line.paidFor[claimId]`, `Policy.claimPaid[claimId]` and
  `Claim.status` are the three guards.
- The central fund cover is capped, one-shot and requires 2-of-3 signatures.
- Global pause must not block settlement, close, expiry or refunds. New-risk arms consult
  `isPaused` and fail closed; `make audit-check` enforces the gate matrix.
- Do not claim a behavioural result unless the suite actually ran. "Implemented" means
  source plus static/parser gates, never behavioural verification.
- Do not modify r-gen, r-cash or r-share from this repository.

## Documentation

- `docs/` is mdBook source; `docs/book/` is generated and gitignored.
- Stock mdBook only. ASCII diagrams.
- Every chapter except `SUMMARY.md` is listed in `SUMMARY.md` exactly once.
- `reference/` is canonical for arms, schemas, constraints and install order.
- Use status labels: "Implemented" is source plus static/parser gates; "Tested" requires a
  named passing suite.
