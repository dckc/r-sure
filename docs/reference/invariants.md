# Invariants

> **Status:** Implemented (source + static/parser gates); Lean proofs are scaffolded.

1. **Capacity**: `committed + written <= capital` and `free >= 0`.
2. **Subscription**: a bound slip has `sum(shareBps) == 10000` and at least one line.
3. **Exposure**: the final line absorbs the aggregate remainder; at bind the exact line
   exposure sum equals the aggregate limit (the quote reserves a conservative cap).
4. **Premium conservation**: `commission + levy + sum(line credits) == premiumTotal`.
5. **Payable**: `payable = max(0, min(agreed, perClaimLimit, aggregateRemaining) - deductible)`.
6. **Settlement conservation**: `sum(line payouts) + fund cover == payable`.
7. **Line conservation**: `paid <= exposure <= written <= capital`; `capital` never negative.
8. **Exactly once**: a claim URI is paid at most once per line, once per policy, and the central
   fund covers it at most once.
9. **Aggregate**: `aggregateRemaining' = aggregateRemaining - payable`, never negative.
10. **No partial settlement**: after a value move, a failure rolls the deploy back.
11. **Terminal states**: settled/denied claims and expired policies cannot be re-opened.
12. **Pause**: global pause does not block settlement, close, expiry or refunds.
