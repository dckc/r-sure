# PolicyBook — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/19_books.rho`
- State cells: policyBookState
- Cross-cell writers: none
- Writers: register
- Readers: policy, policies, byInsured, byBroker, bySlip
- Replay guard: `nonce`
- Bundle publication: top-level, closed

## Review

`register` reads the policy info before taking `policyBookState`, so the cell is not held during the read. The book is never called by `PolicyFactory` or `Policy` (composition gap, HZ-G2). No value moves.

## Await / value-move notes

- Awaits while holding state: register: Policy info before book take
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/19_books.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
