# RiskBook — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/12_risk.rho`
- State cells: riskBookState
- Cross-cell writers: riskMake writes riskBookState
- Writers: submit
- Readers: risk, risks, byInsured, byBroker
- Replay guard: `none`
- Bundle publication: top-level, closed

## Review

`submit` authenticates and validates before `riskMake` consumes `riskBookState`. The book is written by the instance maker (cross-cell writer). The tri-test checks presence only; it does not link evidence or require a numerical probability (composition/business finding).

## Await / value-move notes

- Awaits while holding state: submit: auth/validation then riskMake
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/12_risk.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
