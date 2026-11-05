# Notify and settle a claim

> **Status:** Mapping only.

1. The insured or broker calls `Policy.openClaim` with the loss height, claimed amount and
   evidence. The policy checks the period, notice window and aggregate remaining, then creates
   a `Claim`.
2. The lead manager calls `Claim.classify` (`standard` or `complex`) and `Claim.assess`.
3. For a standard claim, `Claim.agree` by the lead binds the followers. For a complex claim,
   the lead and second must both agree.
4. To contest the assessment, the insured or broker calls `Claim.dispute` with an r-gen
   oracle case request. The adjudicator decides and executes; the claim applies the outcome.
5. `Claim.settle` is permissionless once agreed. The policy computes the payable amount,
   splits it across the lines and pays the insured's r-cash deposit facet.
6. If a syndicate is short, settlement refuses and the claim stays agreed. The central fund
   can cover a capped shortfall with 2-of-3 signatures; a retried settlement pays the rest.
