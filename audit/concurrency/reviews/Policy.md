# Policy — concurrency and composition review

> **Status:** Internal review, updated 2026-11-07. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/17_policy.rho`
- State cells: policyState
- Cross-cell writers: none
- Writers: distribute, openClaim, settleClaim, expire
- Readers: info, terms, lines, line, claims, claim, payable
- Replay guard: `policyToken/claimToken`
- Bundle publication: bundle+{*Policy}; the contract body rebinds state, purse and tokens, and check_bundle_closedness reports no candidates

## Review

`distribute` and `settleClaim` consume `policyState` once and repost on every terminal arm. Their component lookups and value flows are staged in `policyDistribute*` and `policySettle*` helpers that receive the snapshot as data and the cell name only to repost; dispatch depth is 3. `openClaim` peeks the snapshot because ClaimFactory reads the policy back; the claim id is committed by the single consume once the factory replies. `expire` holds the cell across Clock, reposts, and releases the policy lines (F-006). F-020 holds: SureMath.payable is the documented minimum and `settleClaim` propagates a math refusal before any value move; the covered and uncovered branches share `policySettleApply`. `Policy.distribute` is not pause-gated; new policy creation is blocked through the gated syndicate/slip path, so distributing an existing policy remains a value-out path.

## Await / value-move notes

- Awaits while holding state: distribute: SureMath/Distribution, openClaim: ClaimFactory, settleClaim: SureFund/Line.pay, expire: Clock
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/17_policy.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: the 2026-11-07 campaign on the refactored tree passed 38/38 run suites, and the local reducer passes; CI run 42386549218 is green.
