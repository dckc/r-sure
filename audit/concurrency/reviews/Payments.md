# Payments — concurrency and composition review

> **Status:** Internal review, updated 2026-11-07. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/40_payments.rho`
- State cells: paymentsState
- Cross-cell writers: none
- Writers: admin
- Readers: health, ensureAccount, accountOf, depositFacet, issuer, platformOwner
- Replay guard: `nonce`
- Bundle publication: top-level, closed

## Review

`payResolveUri` peeks `paymentsState` and awaits the r-cash Root. The admin arm consumes the cell across `SureAdmin`/`AdminGuard` and delegates to `paymentsApplyAction`, which reposts on success and refusal. `health` is one tuple match on the issuer/facet/account replies. `issuer`/`depositFacet` are per-arm resolves, not cached. A missing r-cash Root remains a hang point for every value path; the match gate is green at depth 3.

## Await / value-move notes

- Awaits while holding state: admin: SureAdmin/AdminGuard, payResolveUri: r-cash Root
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/40_payments.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: the 2026-11-07 campaign on the refactored tree passed 38/38 run suites, and the local reducer passes; CI run 42386549218 is green.
