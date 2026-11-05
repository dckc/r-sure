# RgenAdapter — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/05_rgen.rho`
- State cells: rgenState
- Cross-cell writers: none
- Writers: admin
- Readers: health, config, oracleFactory, credentialFactory, claimFactory, verifyCredential, verifyClaim, verifyProvenance
- Replay guard: `nonce`
- Bundle publication: top-level, closed

## Review

`rgenResolve` peeks `rgenState` for the Root URI and then awaits the r-gen Root. A concurrent admin change could make a read use a stale URI; reads are advisory. `admin` consumes the cell across `AdminGuard`. `verifyProvenance` resolves a URI and calls `Provenance.verify`; a missing or refusing r-gen leaves the caller to handle the refusal.

## Await / value-move notes

- Awaits while holding state: rgenResolve: registry + r-gen Root, admin: AdminGuard
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/05_rgen.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
