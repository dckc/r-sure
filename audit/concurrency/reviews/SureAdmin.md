# SureAdmin — concurrency and composition review

> **Status:** Internal review, updated 2026-11-07. Verdict: **concern**. This is a desk review, not
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

`admin` consumes `adminState`, awaits `AdminGuard.verify`, then reposts; every refusal reposts the snapshot. No re-entrant path. `isPaused` is consulted by the new-risk arms through a per-file fail-closed helper (F-003 fixed); terminal, claims and value-out arms remain exempt. The match gate is green; this term was not part of the 2026-11-07 handler flattening.

## Await / value-move notes

- Awaits while holding state: admin: AdminGuard verify
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/02_admin.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: the last full campaign (2026-11-06) passed the relevant suites; the 2026-11-07 refactor is covered by `make spec-check`, the local reducer and CI run 42386549218. The full campaign must be rerun.
