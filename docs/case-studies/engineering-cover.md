# Engineering project cover

> **Status:** Mapping only. The full journey is a planned behavioural suite.

An engineering project insured for defect and delay risk. The insured's asset has r-gen
claims and validations: each validation pairs a claim (quantity) with a qualified assessor's
verdict (quality) to form a K-Asset. The broker references those K-Assets as underwriting
evidence.

1. The insured submits a `Risk` for class `engineering`, with the project asset reference,
   declared value, period and three insurability answers.
2. The broker opens a `Slip` with a premium, aggregate limit, per-claim limit, deductible and
   a lead-claims basis.
3. Three syndicates subscribe 50/30/20. The lead is the first line.
4. The insured accepts and funds the premium; bind opens the lines and distributes the
   premium.
5. A defect loss is notified. The lead classifies it complex because it exceeds the standard
   threshold; the lead and second assess and agree.
6. Settlement pays 50/30/20 from the three syndicate purses to the insured's r-cash account.
7. A coverage dispute opens an r-gen `OracleCase`; the adjudicator's partial award becomes the
   agreed amount and settlement pays it.

The r-gen evidence is advisory but auditable: the claim records the exact K-Asset URIs and
hashes that the underwriters relied on.
