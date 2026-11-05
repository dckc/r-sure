# r-sure

r-sure is a devnet-only suite of Rholang primitives for a Lloyd's-style subscription
insurance market. It is a sibling of r-gen, r-share and r-cash.

The design is deliberately small: a syndicate is capacity, a slip is a risk offered to
several syndicates, a policy is a bound slip, and a claim is an adjudicated loss paid pro
rata by the subscribing lines. Premiums and payouts settle in r-cash; engineering evidence
comes from r-gen.

> **This is not an insurer and carries no regulatory approval.** Do not use it with real
> funds. Read [Status and scope](orientation/status-and-scope.md) first.

New to insurance or Lloyd's? Start with the primer:

- [Insurance basics](primer/insurance-basics.md)
- [Lloyd's of London for dummies](primer/lloyds-for-dummies.md)
- [Design philosophy: the NAIC/CIPR basis](primer/design-philosophy.md)

## The five moving parts

```
insured ── broker ── slip ── policy ── claim
              │         │        │         │
              ▼         ▼        ▼         ▼
           syndicates  lines   premium   settlement
```

- **Syndicate**: capital, risk appetite and a contract-owned claims purse.
- **Broker**: a registered intermediary that opens slips.
- **Slip**: the placing document. Subscriptions sum to 10000 bps; the first line is the lead.
- **Policy**: the bound slip, with premium distribution and an aggregate limit.
- **Claim**: notification, classification, assessment, agreement and settlement.

The next chapters explain each part and the cash flows between them.
