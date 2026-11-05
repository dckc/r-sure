# Broker — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/11_broker.rho`
- State cells: brokerState
- Cross-cell writers: none
- Writers: addSlip, pause, resume
- Readers: info, profile, slips
- Replay guard: `none`
- Bundle publication: bundle+{*Broker} unclosed: captures brokerState

## Review

`addSlip`, `pause` and `resume` consume `brokerState` and repost without external awaits. `bundle+{*Broker}` captures `brokerState` (P0 bundle). No value moves. `addSlip` is pause-gated; `pause/resume` stay available.

## Await / value-move notes

- Awaits while holding state: none recorded
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/11_broker.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
