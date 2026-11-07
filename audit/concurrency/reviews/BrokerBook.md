# BrokerBook — concurrency and composition review

> **Status:** Internal review, updated 2026-11-07. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/11_broker.rho`
- State cells: brokerBookState
- Cross-cell writers: Broker writes brokerBookState through brokerMake (declared)
- Writers: register, brokerMake
- Readers: brokerOf, brokers
- Replay guard: `none`
- Bundle publication: top-level, closed

## Review

`register` peeks the book and calls `brokerMake`; the maker updates the book directly, and the public `registerDone` callback was removed (F-008). The duplicate-owner path now reposts `brokerBookState` before the refusal, so a second registration no longer empties the book; HZ-037 and RCA-002 record it. `Broker` writes `brokerBookState` through the maker's update (declared cross-cell writer).

## Await / value-move notes

- Awaits while holding state: register: brokerMake
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/11_broker.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: the last full campaign (2026-11-06) passed the relevant suites; the 2026-11-07 refactor is covered by `make spec-check`, the local reducer and CI run 42386549218. The full campaign must be rerun.
