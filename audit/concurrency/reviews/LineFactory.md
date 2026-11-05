# LineFactory — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/14_line.rho`
- State cells: none
- Cross-cell writers: none
- Writers: none
- Readers: create
- Replay guard: `none`
- Bundle publication: publishes Line with unclosed bundle

## Review

Stateless factory. It creates `Line` and publishes it with `bundle+{*Line}`; the bundled body captures `lineState`, the three capabilities and `policyToken` (P0 bundle, HZ-B1). The factory itself has no state.

## Await / value-move notes

- Awaits while holding state: rs bundle publication
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/14_line.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
