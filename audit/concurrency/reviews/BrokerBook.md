# BrokerBook — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/11_broker.rho`
- State cells: brokerBookState
- Cross-cell writers: brokerMake writes brokerBookState via registerDone
- Writers: register, registerDone
- Readers: brokerOf, brokers
- Replay guard: `none`
- Bundle publication: top-level, closed

## Review

`register` peeks the book, calls `brokerMake`, and relies on `registerDone` to consume and repost. `registerDone` is a public arm that accepts an arbitrary `id`/`uri` and can be front-run (P1, HZ-A1). `Broker` writes `brokerBookState` via the callback (cross-cell writer).

## Await / value-move notes

- Awaits while holding state: register: brokerMake
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/11_broker.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
