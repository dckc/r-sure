# Settlement and the central fund

> **Status:** Implemented (source + static/parser gates); the shortfall path is scaffolded.

r-cash is the settlement rail. r-sure does not hold balances in a database; it holds
contract-owned ERTP purses for premium and claims, and it uses r-cash accounts only for
deposits and withdrawals.

## Syndicate purse

A syndicate's claims purse holds members' capital and credited premiums. A line's `pay`
capability withdraws exactly its share and deposits it into the insured's r-cash deposit
facet. The syndicate state records capital, written lines, premiums and claims paid.

```
free = capital - committed - written
```

A claim payment reduces `capital` and `written` by the same amount, so `free` is unchanged
and capital cannot go negative (`paid <= exposure <= written <= capital`).

## Central fund

At Lloyd's, the Central Fund is the last layer of the chain of security: a market-level fund
governed by the Council, available at its discretion if a member cannot meet its liabilities.
It is not an ordinary insurance policy and it is not a guarantee that every claim is paid
automatically. The layers before it are the syndicate's assets, the members' funds at
Lloyd's, and the Corporation's central assets. See [Lloyd's of London for
dummies](../primer/lloyds-for-dummies.md) for the full chain.

r-sure deliberately simplifies that to two layers: the syndicate claims purse, then
`SureFund`. `SureFund` receives the premium levy and pays a capped, one-shot shortfall with
2-of-3 admin signatures. The claim reads `covered(claimId)`; a retried settlement subtracts
the cover before paying the lines, so

```
sum(line payouts) + fund cover == payable
```

The fund is a governed safety net, not an automatic payer. That matches the discretionary
character of Lloyd's central fund support and avoids an unauthorised drain path.

## Failure discipline

Before a value move, a refusal returns `(false, reason)`. After a withdrawal or deposit, an
unexpected branch calls `1/0`, which rolls the whole deploy back. A failed settlement leaves
the claim agreed and retryable; it never leaves a partial payout.
