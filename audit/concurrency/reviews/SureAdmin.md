# SureAdmin — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/02_admin.rho`
- State cells: adminState
- Cross-cell writers: none
- Writers: admin
- Readers: keys, isPaused, nonce
- Replay guard: `nonce`
- Bundle publication: top-level, closed

## Review

`admin` consumes `adminState`, awaits `AdminGuard.verify`, then reposts. No re-entrant path. `isPaused` is a read arm but no mutating arm consults it (dead pause, HZ-E1).

## Await / value-move notes

- Awaits while holding state: admin: AdminGuard verify
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/02_admin.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
