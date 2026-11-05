# Claim — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/18_claim.rho`
- State cells: claimState
- Cross-cell writers: none
- Writers: addEvidence, classify, assess, agree, dispute, settle, close
- Readers: info, evidence
- Replay guard: `claimToken/status`
- Bundle publication: bundle+{*Claim} unclosed: captures claimState/token

## Review

`settle` and `dispute` take `claimState` and later take it again after external awaits without a repost (P0, HZ-C5). `classify` and `assess` hold the cell across `claimPolicyInfo`. `applyDecision` is a private closure capability and is correctly one-shot via the oracle case. `bundle+{*Claim}` is unclosed.

The Lean model exposes a further P1: `agree` and `addEvidence` do not reject every terminal status, so a settled claim can be re-agreed (F-021, HZ-027). `claim_agree_terminal_gap` is the counterexample; INV-10 is `partial`, not covered.

## Await / value-move notes

- Awaits while holding state: classify/assess: Policy info, dispute: RgenAdapter/OracleFactory, settle: Policy.settleClaim
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/18_claim.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
