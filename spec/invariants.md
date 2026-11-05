# Invariants

The canonical list is in `docs/reference/invariants.md`. This file is the formal target.

1. Capacity: `committed + written <= capital`; `free = capital - committed - written >= 0`.
2. Subscription: a bound slip has `sum(shareBps) = 10000` and at least one line.
3. Exposure: `sum(line exposure) = aggregateLimit` at bind.
4. Premium: `commission + levy + sum(line credits) = premiumTotal`.
5. Payable: `payable = max(0, min(agreed, perClaimLimit, aggregateRemaining) - deductible)`.
6. Settlement: `sum(line payouts) + fund cover = payable`.
7. Line: `paid <= exposure <= written <= capital`.
8. Exactly once: per claim per line, per claim per policy, per claim per fund.
9. Aggregate: `aggregateRemaining' = aggregateRemaining - payable >= 0`.
10. Terminal: a settled/denied claim or expired policy cannot be re-opened.
11. Atomicity: no partial value move survives a failed deploy.
12. Pause: settlement, close, expiry and refunds are not blocked by global pause.
