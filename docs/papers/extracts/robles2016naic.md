# @robles2016naic — Insurance: The Highest and Best Use Case for Blockchain Technology

**Citation.** Daniel R. Robles, PE, MBA, "Insurance: The Highest and Best Use Case for
Blockchain Technology," NAIC Center for Insurance Policy and Research (CIPR) Newsletter,
July 2016, printed pp. 17–27 (PDF pp. 1–11).

**Standing.** An opinion column. The article states that the views are the author's and not
the official position of the NAIC or its members (p. 17; repeated on p. 27). It is a design
ancestor, not a standard or a specification.

**Text note.** The PDF's embedded text layer drops some fi/fl/ti ligatures. The quotations
below are reconstructed to standard spelling; wording and page numbers are otherwise
unchanged.

## p. 17 — the problem and the thesis

> "The purpose of this article is to introduce the reader to blockchain technology and to
> explore how it may be used to assist with identifying and facilitating risk transfers in
> the insurance industry."

> "The primary objective of blockchain technology should be to reduce the cost of capital by
> the decentralization of risk."

> "Wherever the insurance industry is capable of pooling project risks, the cost of capital
> is greatly reduced."

> "This article suggests the place to begin developing blockchain technology is through a
> consortium of insurance and professional engineering entities in the creation of relevant
> infrastructure and its derivatives upon which everyone depends."

## p. 20 — the three insurability questions

> "Can we identify the risk exposure?
> What is the (mathematical) probability such risk exposure will manifest?
> If so, what are the consequences (cost) of failure?"

> "The rules of our test are simple: All three conditions must be known in order to create
> an insurance product. The inability to answer any one of these questions results in a
> non-insurable condition. Non-insurable business methods using blockchain technology must
> then be augmented or rejected."

> "Our theory is if each component part is insurable then the entire ecosystem should be
> insurable."

**Why it matters.** These are the source questions behind r-sure's `Risk.triTest`
(`exposureRef`, `probabilityBasis`, `consequenceBasis`, `consequenceRef`). The four-field
split and the scoring model come from r-gen's legacy `RiskMath.rho`; r-sure checks presence,
not numerical quality.

## p. 22 — money and property caveat

> "So there we have it. All three are insurable and, therefore, we can say with rational
> confidence blockchains are insurable for their intended outcome. The problem is blockchains
> cannot exist in digital isolation; their value must be derived from the value of something
> else—something real."

> "The answer for all practical purposes is that cryptocurrencies cannot really be treated as
> property, at least within the boundaries of law. Therefore, they are uninsurable."

**Why it matters.** r-sure settles in r-cash tokens but takes no position on their legal
status. The paper's caveat is part of the reason the repository is explicitly devnet-only.

## p. 23–24 — the engineering bridge

> "For 80 years, the professional engineers (PEs) have been trusted third-party adjudicators
> for banks and insurance companies."

> "During the design and construction phase of a project, the asset lives on a balance sheet
> only as an engineering design. The engineering stamp serves as proxy for the future title
> and revenue of the project. Insurability is contingent on engineering sign-off."

**Why it matters.** r-gen's claims, validations, K-Assets and credentials are the repository's
engineering evidence; r-sure references them but does not reproduce the PE-stamp legal
function.

## p. 25 — the adjudicator and the caveat on the bank-led path

> "An Oracle contract is an adjudicated contract with the added requirement the adjudicator
> … is deemed the most appropriate person to be performing the adjudication."

> "The Oracle must make decisions in physical space—not simply assess digital data. The
> Oracle must be able to be present in time and space, determine causation of an event and
> deal with significant ambiguity in relation to the facts being observed. The validity of
> the Oracle is what establishes tangibility and invokes law—therefore, money and property."

> "The current path of blockchain deployment dominated by banks, venture capitalists and
> decentralized autonomous organizations is not sufficient in delivering the highest and best
> use for this important technology within the existing framework."

**Why it matters.** r-sure's optional `Claim.dispute` path opens an r-gen `OracleCase` with a
credential-proved adjudicator and applies the decision through the claim's private
`applyDecision` capability.

## pp. 25–26 — the hybrid/insurance umbrella

> "The superior method for so-called 'controlling' blockchain technology would be through
> hybrid application of digital and physical proofing mechanisms that are individually
> insurable so that their infinite combinations would still result in easily insurable
> enterprise. Reinsurance could then be an umbrella."

**Why it matters.** r-sure does not implement reinsurance or a hybrid proof-of-physical
mechanism. It implements a subset: a risk record, evidence references, an adjudication
capability and a capital backstop.

## What the extract does not claim

The paper does not prescribe r-sure's Lloyd's-style subscription market, its r-cash
settlement, its data schemas, its four-field tri-test, its scoring model, or its central
fund. It is a thesis about insurance, engineering and the cost of capital. The primer's
"What this paper does not say" section lists the boundary.
