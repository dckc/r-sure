# Risk — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/12_risk.rho`
- State cells: riskState
- Cross-cell writers: none
- Writers: addEvidence, assess, accept, decline, expire
- Readers: info, evidence
- Replay guard: `nonce`
- Bundle publication: bundle+{*Risk} unclosed: captures riskState

## Review

`expire` consumes `riskState`, awaits Clock, then reposts. `assess` accepts an arbitrary assessment map; it does not validate the quoted premium or the credential (P2). `bundle+{*Risk}` captures `riskState` (P0 bundle).

## Await / value-move notes

- Awaits while holding state: expire: Clock
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/12_risk.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
