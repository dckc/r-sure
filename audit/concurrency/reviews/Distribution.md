# Distribution — concurrency and composition review

> **Status:** Internal review, updated 2026-11-07. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/15_distribution.rho`
- State cells: distState
- Cross-cell writers: none
- Writers: run
- Readers: info, plan, paid
- Replay guard: `one-shot status/token`
- Bundle publication: bundle+{*Distribution}; the contract body rebinds state, purse and token, and check_bundle_closedness reports no candidates

## Review

`run` consumes `distState`, runs `allocPlan` and `payPlan` (including value moves), and reposts on success and on every refusal; unexpected branches after a value move call `1/0`. `payAccount` is staged in `payAccountMove`, and the match refactor flattened `run` to depth 3. `distState` is held across the value moves, which is the documented P2 pattern for this arm.

## Await / value-move notes

- Awaits while holding state: run: allocPlan/payPlan across value moves
- Value moves: payAccount, payFund, payLine
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/15_distribution.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: the 2026-11-07 campaign on the refactored tree passed 38/38 run suites, and the local reducer passes; CI run 42386549218 is green.
