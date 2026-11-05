# Place a risk

> **Status:** Mapping only. The CLI and devnet journey are scaffolds.

1. The insured submits a risk with `RiskBook.submit`: class, asset reference, declared value,
   requested limit and deductible, period, evidence and the three insurability answers.
2. A registered broker opens a slip with `SlipFactory.open`, passing the risk id and the
   coverage terms. The terms are validated by `CoverTerms` and hashed.
3. Each syndicate manager calls `Slip.subscribe` with its share. The slip calls
   `Syndicate.quote`, which reserves capacity and returns a one-shot `LineGrant`.
4. The insured calls `Slip.accept`.
5. When the shares sum to 10000, the insured calls `Slip.fundPremium` with a payment from
   their r-cash account.
6. Anyone may call `Slip.bind`; it opens the lines, creates the policy and distributes the
   premium.
