# SureRoot — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/00_root.rho`
- State cells: rootState
- Cross-cell writers: none
- Writers: register, rotate, deprecate, freeze, admin
- Readers: resolve, get, keys, nonce, resolveMany
- Replay guard: `govNonce`
- Bundle publication: top-level, closed

## Review

`register` consumes `rootState`, awaits `dops.pubKeyBytes`, then reposts the consumed snapshot. The deploy is atomic and no re-entrant call reaches `SureRoot`, but the cell is held across an external await (P2/P4 concern). `admin` holds the cell across `AdminGuard.verify`; the nonce check is on the snapshot.

## Await / value-move notes

- Awaits while holding state: register: dops pubKeyBytes, admin/rotate/deprecate/freeze: AdminGuard
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/00_root.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
