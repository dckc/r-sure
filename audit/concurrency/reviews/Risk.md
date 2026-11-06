# Risk — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/12_risk.rho`
- State cells: riskState
- Cross-cell writers: none
- Writers: addEvidence, assess, accept, decline, expire
- Readers: info, evidence, variance
- Replay guard: `nonce`
- Bundle publication: bundle+{*Risk} unclosed: captures riskState

## Review

`expire` consumes `riskState`, awaits Clock, then reposts. `assess` peeks `riskState`, validates the assessment, awaits r-gen and SureMath, then consumes with a nonce check and refuses `stale` if the cell moved; it computes the engineering/insurer gap and the loaded-premium floor. `accept` records the variance acknowledgement. `bundle+{*Risk}` captures `riskState` (the intended private capability). `RiskBook.submit`, `accept` and `decline` are pause-gated; `addEvidence`, `assess` and `expire` stay exempt.

## Await / value-move notes

- Awaits while holding state: expire: Clock; assess claims no hold across its r-gen/SureMath awaits (peek, then nonce-checked commit)
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/12_risk.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: `harness/unit_variance.py` and `harness/unit_risk.py` pass on devnet; the local reducer exercises the same flow.
