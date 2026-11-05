# Policy — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/17_policy.rho`
- State cells: policyState
- Cross-cell writers: none
- Writers: distribute, openClaim, settleClaim, expire
- Readers: info, terms, lines, line, claims, claim, payable
- Replay guard: `policyToken/claimToken`
- Bundle publication: bundle+{*Policy} unclosed: captures policyState/purse/tokens

## Review

`distribute`, `openClaim` and `settleClaim` take `policyState` and later take it again after external awaits without a repost (P0, HZ-C4). `expire` does not release the policy lines, so capacity remains written (P1, HZ-L1). `openClaim` does not check the loss period or notice window (P1). `bundle+{*Policy}` is unclosed.

The Lean model exposes a further P1: `settleClaim` does not guard `payable <= aggregateRemaining`, so the aggregate can underflow (F-020, HZ-026). `policy_settle_aggregate` proves the update only under the missing guard; INV-9 is `partial`, not covered.

## Await / value-move notes

- Awaits while holding state: distribute: SureMath/Distribution, openClaim: ClaimFactory, settleClaim: SureFund/Line.pay, expire: Clock
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/17_policy.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
