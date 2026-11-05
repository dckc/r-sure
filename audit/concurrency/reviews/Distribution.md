# Distribution — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/15_distribution.rho`
- State cells: distState
- Cross-cell writers: none
- Writers: run
- Readers: info, plan, paid
- Replay guard: `one-shot status/token`
- Bundle publication: bundle+{*Distribution} unclosed: captures distState/purse/token

## Review

`run` takes `distState`, runs `allocPlan`/`payPlan` (including value moves), then takes the same cell again without a repost (P0 take-await-take, HZ-C2). `payAccount`/`payFund`/`payLine` withdraw and deposit; unexpected branches use `1/0` after the value move. `bundle+{*Distribution}` is unclosed.

## Await / value-move notes

- Awaits while holding state: run: allocPlan/payPlan across value moves
- Value moves: payAccount, payFund, payLine
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/15_distribution.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
