# Design philosophy: the NAIC/CIPR basis

> **Status:** Primer (stable). A design rationale, not a specification or a compliance
> claim.

r-sure is an engineering exercise: can a small set of Rholang primitives express the
Lloyd's subscription market, with premiums and claims settled on r-cash and engineering
evidence supplied by r-gen? The starting point for that question is a 2016 NAIC/CIPR
newsletter article by Daniel R. Robles, *"Insurance: The Highest and Best Use Case for
Blockchain Technology."* This chapter explains what the paper argues, what r-sure took from
it, and — just as important — what it did not take.

## 1. Provenance and standing

**Citation.** Daniel R. Robles, PE, MBA, "Insurance: The Highest and Best Use Case for
Blockchain Technology," *NAIC Center for Insurance Policy and Research (CIPR) Newsletter*,
July 2016, printed pp. 17–27 (PDF pp. 1–11). The article is an opinion column. The first page
says:

> "The views expressed in this article are the opinions of the author. This article is not
> meant to represent the official position of the NAIC or its members." — p. 17

The back page repeats that the publication's views are not necessarily those of the NAIC.
The paper is therefore a **design ancestor and a source of questions**, not a standard, a
model regulation, or a specification. r-sure does not claim NAIC endorsement or regulatory
compliance.

The paper is archived at `docs/papers/NAIC_CIPR_2C_20July_2016.pdf`; the quotations used
here are extracted in `docs/papers/extracts/robles2016naic.md`. The PDF's text layer drops
some ligatures, so the extract marks reconstructed spelling.

## 2. The problem the paper targets

Robles starts from a practical complaint: computer databases cannot talk to each other
without "a layer of expensive fault-prone human administration or bureaucracy" (p. 17).
Blockchain offers shared, immutable records and removes some of that reconciliation work.
But the point is not a currency. The point is capital:

> "The primary objective of blockchain technology should be to reduce the cost of capital by
> the decentralization of risk." — p. 17

Insurance is the mechanism that pools risk and therefore lowers the cost of capital:

> "Wherever the insurance industry is capable of pooling project risks, the cost of capital
> is greatly reduced." — p. 17

That is the paper's title claim. It is an economic thesis, not a smart-contract design.

## 3. Why insurance and engineering, not banking alone

The paper argues that blockchain should not be "the exclusive domain of a single sector, such
as banking, nor venture-funded start-ups with ultra-high return on investment (ROI)
requirements" (p. 17). It proposes a consortium of insurers and professional engineering
entities because the value of a physical project is established by engineering evidence:

> "The engineering stamp serves as proxy for the future title and revenue of the project.
> Insurability is contingent on engineering sign-off." — p. 24

Professional engineers, in the paper's account, have been "trusted third-party adjudicators
for banks and insurance companies" for 80 years (p. 23). The paper's bridge is therefore
insurance + engineering + an adjudicator who can decide in physical space, not just inspect
digital data.

r-sure's version of that bridge is deliberately thin:

- r-gen supplies engineering claims, validations, K-Assets, credentials and provenance.
- r-sure stores evidence references (URIs and hashes) on the risk and the claim.
- an optional r-gen `OracleCase` lets a credential-proved adjudicator decide a disputed
  claim and execute the decision through the claim's private `applyDecision` capability.

r-sure does not verify that an engineering stamp is legally valid, and it does not implement
the paper's consortium.

## 4. The three insurability questions

The paper's most concrete contribution is a three-question test:

> "Can we identify the risk exposure?
> What is the (mathematical) probability such risk exposure will manifest?
> If so, what are the consequences (cost) of failure?" — p. 20

And the rule:

> "All three conditions must be known in order to create an insurance product. The inability
> to answer any one of these questions results in a non-insurable condition. Non-insurable
> business methods using blockchain technology must then be augmented or rejected." — p. 20

This is the seed of r-sure's `Risk` submission. The contract stores four fields:

| Paper question | r-sure field | What the contract checks |
|---|---|---|
| Identify the exposure | `exposureRef` | non-empty string |
| Probability it manifests | `probabilityBasis` | non-empty string |
| Consequences / cost | `consequenceBasis` and `consequenceRef` | both non-empty |

The four-field split comes from r-gen's legacy `RiskMath.rho`, not from the paper. r-sure
checks **presence**, not quality: it does not require a numerical probability, a monetary
consequence, or a link between a tri-test field and the evidence list. The paper's
"non-insurable" rule is therefore implemented as "missing/empty field -> refuse
`RiskBook.submit`", not as an underwriting opinion.

```
paper: three questions
        │
        ▼
r-gen RiskMath: four fields + S×P×E score
        │
        ▼
r-sure Risk.triTest: four non-empty fields
```

That is a deliberate simplification. A production system would need a qualified
underwriter, a pricing model and a quality gate; r-sure provides the durable record and the
refusal primitive, not the judgement.

## 5. The oracle as an adjudicated contract

The paper's adjudication idea is that a decision must be made by the person best placed to
make it, not by a generic panel:

> "An Oracle contract is an adjudicated contract with the added requirement the adjudicator
> … is deemed the most appropriate person to be performing the adjudication." — p. 25

and:

> "The Oracle must make decisions in physical space—not simply assess digital data. The
> Oracle must be able to be present in time and space, determine causation of an event and
> deal with significant ambiguity in relation to the facts being observed. The validity of
> the Oracle is what establishes tangibility and invokes law—therefore, money and property."
> — p. 25

r-sure does not implement a general oracle network. It reuses r-gen's `OracleFactory` /
`OracleCase`:

1. the insured or broker opens a dispute with a named adjudicator and a credential URI;
2. r-gen checks the adjudicator's credential at decision time;
3. the adjudicator decides `uphold`, `partial` or `revoke`;
4. `OracleCase.execute` calls the claim's private `applyDecision` capability;
5. the claim maps the outcome to an agreed amount and settlement proceeds.

The claim's apply capability is created in the claim's closure and passed to the oracle
case. It is one-shot and bound to the claim URI. That is the paper's "most appropriate
person" idea expressed as a capability, not as a reputation system.

## 6. Caveats the paper itself raises

The paper is not a naive "code is law" essay. It raises the problems that make insurance
hard:

- **Human judgement**: "it is extremely difficult for a computer to make human-like
  decisions, and the full breadth of human capability is still well outside the reach of
  blockchains" (p. 18). Its answer is an adjudicator who can act in physical space.
- **Institutional knowledge**: the paper warns that eliminating administrative staff can
  destroy the knowledge an insurer needs (p. 20).
- **Money and property are not automatically insurable**: "cryptocurrencies cannot really be
  treated as property, at least within the boundaries of law. Therefore, they are
  uninsurable" (p. 22). r-sure settles in r-cash tokens and takes no position on their legal
  status.
- **Regulation**: the paper worries about regulatory overreach and about what happens when
  "the human is taken out of the equation" (p. 20). r-sure is explicitly not regulated and
  not an insurer.
- **The market is not only insurance**: the paper's claim is that the bank/VC/DAO-led path
  "is not sufficient in delivering the highest and best use" (p. 25), not that insurance is
  the only possible use.

These caveats are why r-sure keeps the optional oracle path, the human-controlled central
fund and the explicit "not an insurer" warning. They are also why the audit treats
capability and authority questions as first-class.

## 7. What this paper does not say

It is easy to over-read a 2016 essay. The following are **not** in the paper:

- a Lloyd's-style subscription market or a placing slip;
- r-cash, ERTP purses, deposit facets, or any settlement rail;
- smart-contract enforcement of premium and claims;
- the four-field `triTest` schema or the `severity × probability × exposure` scoring model
  (those come from r-gen);
- a recommendation to use RChain or rholo (the chain did not exist in its current form);
- a legal opinion that r-cash tokens are money or property;
- a consortium implementation, a coverholder model, or a reinsurance contract;
- a claim that insurance is the *only* use of blockchain.

r-sure implements a subset of the paper's **concepts** — risk pooling, an insurability
record, evidence, adjudication, and a capital backstop — using a market structure (Lloyd's)
and a settlement rail (r-cash) that the paper does not describe. The paper is the "why" and
the questions; the Lloyd's primer is the "how"; the contract reference is the "what".

## 8. Design consequences

Three design choices follow from taking the paper seriously without treating it as a
specification:

1. **Record the questions, not only the answers.** `Risk` preserves the exposure,
   probability and consequence basis even when an underwriter declines. The record is
   auditable after the fact.
2. **Make adjudication explicit.** A claim is not settled by a caller asserting an amount;
   it is classified, assessed, agreed and, if disputed, adjudicated by a credential-proved
   person. The capability path is visible.
3. **Keep a capital backstop.** A syndicate purse can be exhausted. `SureFund` provides a
   governed, capped, one-shot shortfall cover rather than an automatic bailout, and the
   settlement path reads the cover before paying the lines.

Those choices are not proofs. They are design commitments that the concurrency and
composition audit must test: a record is only useful if the cells survive, and an
adjudication is only binding if the capability cannot be replayed or redirected.

> **Further reading.** The paper extract is at
> [`../papers/extracts/robles2016naic.md`](../papers/extracts/robles2016naic.md); the
> citation and hash are in [`../papers/manifest.json`](../papers/manifest.json). The
> [Lloyd's primer](lloyds-for-dummies.md) explains the market structure; the
> [claims chapter](../concepts/claims-and-adjudication.md) explains the on-chain path.
