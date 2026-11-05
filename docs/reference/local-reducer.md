# Local reducer

> **Status:** Implemented. Installs all 17 terms and drives a placement and claim to
> settlement; it is a development gate, not a replacement for the devnet campaign.

`make local-reducer` runs the built contracts in the node's own in-memory `RhoRuntime`.
No devnet, Docker or network is involved. The gate installs `contracts/build/*.rho` in the
install order, then drives:

1. `SureRoot.resolve` and `SureMath.share`;
2. syndicate create, capital contribution and broker registration;
3. risk submit and slip open;
4. subscribe, accept, fund the premium and bind;
5. claim open, classify, assess, agree, settle and close.

It then runs 22 refusal vectors and asserts the exact reason: bind one-shot, settle and
classify after close, terminal agree and evidence, unknown component, duplicate register,
non-installer register, duplicate syndicate and broker, admin replay and below-threshold,
non-insured claim, loss outside the window, zero claim, blank and asset-less terms, settle
before agreement, assess before classification, non-lead agree, and unknown policy/book
claims.

## What it catches

- Install-time normalizer failures: free variables, name/data sort errors, wildcard or
  bundle-content errors.
- Registry and install wiring: every component must register under its key.
- Call-shape and lifecycle errors: every step asserts a `true` reply and the expected
  state at the end (21 components, claim `closed`, `paid` 800).
- Refusal drift: a changed guard or reason string fails the run, so the negative paths are
  checked before the devnet campaign sees them.

It caught the funding term's missing `wdCh` binder class of defect before any deploy, and
it is the first place a malformed install term or a deadlocked arm fails without bringing
up a node.

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
local-reducer: bound slp:… -> (true, `rho:id:…`)
local-reducer: claim … settled and closed
local-reducer: refused bind is one-shot -> closed
local-reducer: refused non-lead agree -> not lead
local-reducer: root keys -> 21 components
```

## Fixtures and limits

- **Stub r-cash.** `16_fund.rho` creates its purse at install, and the placement needs an
  asset resolver, issuer, purse, account factory and deposit facets. The reducer registers
  a stub r-cash root with those capabilities before the install. The stub returns 6000 for
  a capital contribution, 1000 for `"premium:1000"`, and the requested amount on
  `withdraw`; it does not model ERTP conservation, balances or authority.
- **No signatures.** The deployer id is a fixed public key supplied through the normalizer
  environment; 2-of-3 admin flows and anything that verifies a signature are not exercised.
- **No finality or persistence.** Each run starts from an empty space and ends when the
  calls return. It does not prove a block can be proposed or that state survives a restart.
- **Not a refinement.** The Lean model is separate: this runs the real terms, but it does
  not prove them.
