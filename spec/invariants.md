# Invariants

The canonical list is in `docs/reference/invariants.md`. This file is the formal target.
The Lean names are in `spec/lean/claims.yaml` and `spec/lean/RSure/Invariants.lean`.

| ID | Invariant | Formal predicate |
|---|---|---|
| INV-1 | Capacity | `committed + written <= capital` and `free = capital - committed - written >= 0`. |
| INV-2 | Subscription | A bound slip has `sum(shareBps) = 10000` and at least one line. |
| INV-3 | Exposure | At bind, `sum(line exposure) = aggregateLimit`; the last line absorbs the allocation remainder. |
| INV-4 | Premium | `commission + levy + sum(line credits) = premiumTotal`. |
| INV-5 | Payable | `payable = max(0, min(agreed, perClaimLimit, aggregateRemaining) - deductible)` for the cases the contract implements. |
| INV-6 | Settlement | `sum(line payouts) + fund cover = payable`. |
| INV-7 | Line | `paid <= exposure <= written <= capital`. |
| INV-8 | Exactly once | Per claim per line, per claim per policy, per claim per fund. |
| INV-9 | Aggregate | `aggregateRemaining' = aggregateRemaining - payable >= 0`. |
| INV-10 | Terminal | A settled/denied claim or expired policy cannot be re-opened or re-paid. |
| INV-11 | Atomicity | No partial value move survives a failed deploy. |
| INV-12 | Pause | Settlement, close, expiry and refunds are not blocked by global pause. |

## Model scope

INV-3 and INV-7 are stated over the allocation and line models: the plan sums exactly when
the contract's `paid == amount` guard succeeds, and line exits are guarded by
`paid <= exposure`. INV-5 follows the contract's branch order, which differs from the
three-way `min` in the prose description when `agreed >= perClaimLimit` and
`aggregateRemaining < perClaimLimit`. INV-10 is a target, not a current guarantee: the claim
contract's `agree` and `addEvidence` arms do not reject every terminal state. INV-11 and
INV-12 are explicit boundaries: native ERTP moves and the global pause gate are assumed,
not proved, while F-003 remains open.
