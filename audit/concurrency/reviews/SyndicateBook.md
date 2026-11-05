# SyndicateBook — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/10_syndicate.rho`
- State cells: syndicateBookState
- Cross-cell writers: syndicateMake writes syndicateBookState
- Writers: create
- Readers: syndicateOf, syndicates, byClass, count, verify
- Replay guard: `none`
- Bundle publication: top-level, closed

## Review

`create` peeks `syndicateBookState` for a duplicate owner, awaits `makePurse`, then consumes the book state in `syndicateMake` and reposts. The cell is written by the instance maker, not the book contract (cross-cell writer). `verify` always returns `(true, false)` (fake verification, HZ-S1). A create that fails after reserving a purse leaves an orphan contract, not a capacity leak.

## Await / value-move notes

- Awaits while holding state: create: makePurse, dops
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/10_syndicate.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
