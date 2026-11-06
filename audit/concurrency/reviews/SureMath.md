# SureMath — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **safe-by-inspection**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/04_math.rho`
- State cells: none
- Cross-cell writers: none
- Writers: none
- Readers: bpsSum, share, lineExposures, premiumSplit, lineShares, payable, settlePlan
- Replay guard: `none`
- Bundle publication: top-level, closed

## Review

Stateless or pure component. It has no owned mutable cell; the review checks reply shape, purity, and that it cannot be used to bypass a state owner.

## Await / value-move notes

- Awaits while holding state: none recorded
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/04_math.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).

## Variance arms (2026-11-06)

`varianceRate`, `varianceGap`, `loadedPremium` and `varianceStats` are pure readers: no state cell, no capability, no await beyond their own recursive helpers. `varianceStats` is bounded to 1..16 positive values and returns both the rate and the unscaled numerator for vector comparison. Vectors are executed by the local reducer and by `harness/unit_variance.py`.
