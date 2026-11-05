# Local reducer

> **Status:** Implemented. Installs all 17 terms and calls the registry and `SureMath`;
> it is a development gate, not a replacement for the devnet campaign.

`make local-reducer` runs the built contracts in the node's own in-memory `RhoRuntime`.
No devnet, Docker or network is involved. The gate installs `contracts/build/*.rho` in the
install order, then calls the root and a component arm and checks the replies.

## What it catches

- Install-time normalizer failures: free variables, name/data sort errors, wildcard or
  bundle-content errors.
- Registry and install wiring: every component must register under its key.
- Call-shape errors: a term that resolves a component and calls an arm must get the
  expected reply, or the step reports the reduction error and the reply text.

It caught the funding term's missing `wdCh` binder class of defect before any deploy, and
it is the first place a malformed install term fails without bringing up a node.

## How it runs

```sh
make build            # render contracts/build from contracts/src
make local-reducer
```

Requirements: an RNodeRust checkout at `../RNodeRust` (or `RCHAIN_RUST_DIR`) and
`protoc`, which the node's model crate needs. The script generates a temporary crate under
`.devnet/local-reducer` and builds against the node's workspace, so the reduction semantics
are the node's, not a reimplementation.

The output ends with:

```text
local-reducer: resolve component:clock -> (true, `rho:id:…`, 1)
local-reducer: suremath share(1000, 250) -> (true, 25, 975)
local-reducer: root keys -> 21 components
```

## Fixtures and limits

- **Stub r-cash.** `16_fund.rho` creates its purse at install and resolves
  `component:asset-resolver` through the r-cash root. The reducer registers a stub root with
  an asset resolver, issuer and purse before the install. The stub is enough for install and
  for arms that only create a purse; it does not model ERTP transfers, so premium, payout
  and contribution flows still need r-cash on a devnet.
- **No signatures.** The deployer id is a fixed public key supplied through the normalizer
  environment; 2-of-3 admin flows and anything that verifies a signature are not exercised.
- **No finality or persistence.** Each run starts from an empty space and ends when the
  calls return. It does not prove a block can be proposed or that state survives a restart.
- **Not a refinement.** The Lean model is separate: this runs the real terms, but it does
  not prove them.
