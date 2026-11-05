# Insurance basics

> **Status:** Primer (stable). Educational simplification, not advice or a regulatory
> description.

Insurance is a way to move the cost of an uncertain loss from one party to a pool of parties
who agree to share it. The insured pays a **premium**; the insurer accepts a defined **risk**
and promises to pay a **claim** if a covered event happens. Everything else — underwriting,
limits, deductibles, claims handling, capital and reinsurance — exists to make that promise
credible and priced.

This chapter explains the vocabulary an r-sure reader needs before reading the contract
reference. The [Lloyd's primer](lloyds-for-dummies.md) then explains the market structure,
and [Design philosophy](design-philosophy.md) explains why the repository uses the
NAIC/CIPR paper as a design ancestor.

## 1. Risk is not just "danger"

In insurance, **risk** has three parts:

1. **Exposure** — what can be lost, and to whom. A building, a project, a shipment, a
   liability to a third party, or the revenue lost while a project is delayed.
2. **Probability** — how likely the loss event is, ideally expressed numerically over a
   period.
3. **Consequence** — how much the loss costs if it happens.

A risk is **insurable** only when all three can be described. If nobody can say what is
exposed, how likely the event is, or what the failure costs, the risk is not ready to be
insured. This is the three-question test used by the NAIC/CIPR paper and, in simplified
presence-only form, by r-sure's `Risk` submission.

Two other ideas matter:

- **Insurable interest**: the insured must suffer a real loss if the event happens. You
  cannot insure a stranger's building and profit from its destruction.
- **Moral hazard and adverse selection**: insurance can change behaviour. A deductible makes
  the insured retain part of a small loss; underwriting and exclusions keep the pool from
  being selected only by the worst risks.

```
             risk transfer
 insured  ─────────────────▶  pool of premium
   │                              │
   │ premium                      │ pays covered claims
   ▼                              ▼
 insurer/syndicate  ◀────────  claim fund
```

## 2. Premium is the price of the promise

A premium is not a savings deposit. It is the price of accepting the risk, built from:

- expected claims (frequency × severity);
- expenses (distribution, administration, claims handling);
- the cost of holding capital against unexpected losses;
- a margin for uncertainty and profit.

The insurer earns the premium over the policy period. If the policy is cancelled early, an
**earned premium** calculation decides how much the insurer keeps and how much is returned.
r-sure currently funds the full premium before binding and does not implement instalments or
pro-rata cancellation; those are recorded as out of scope.

## 3. The policy is the contract

A policy is the document that turns a risk into a promise. It normally states:

| Term | Meaning |
|---|---|
| Insured / policyholder | who is protected |
| Period | when cover starts and ends |
| Coverage / perils | what events are covered, and what is excluded |
| Sum insured / limit | the most the insurer will pay |
| Per-claim limit | the most for one loss |
| Aggregate limit | the most for all losses in the period |
| Deductible / excess | the part of each loss the insured retains |
| Premium | the price and payment schedule |
| Conditions | duties such as notice, proof of loss, and cooperation |
| Claims basis | who may agree a claim and how |

The **deductible** is not a penalty. It removes small claims that cost more to administer
than to pay, and it keeps the insured careful. The **limit** caps the insurer's exposure so
the premium and capital can be priced. The difference between per-claim and aggregate limits
matters: a policy can pay several claims, but never more than the aggregate.

r-sure's `CoverTerms` validates these fields; `Policy.payable` applies the per-claim limit,
the remaining aggregate and the deductible.

## 4. Underwriting is the decision to accept risk

**Underwriting** is the process of deciding whether to accept a risk, on what terms, and at
what price. It has four levers:

1. **Selection** — accept, decline, or ask for more information.
2. **Pricing** — set the premium.
3. **Terms** — limits, deductibles, exclusions, warranties, conditions.
4. **Capacity** — how much of the risk the underwriter can carry.

Underwriting is not a single signature. In a subscription market, a **lead** underwriter
negotiates the terms and a **following** market accepts a share. The lead's work is only
useful if the followers can rely on the same terms.

r-sure separates the **risk submission** (`Risk`), the **placing slip** (`Slip`), and the
**subscription** (`Syndicate.quote` / `LineGrant`). The syndicate's capacity is its capital;
a quote reserves a share of that capacity, and binding converts the reservation into a
written line.

## 5. Subscription: many shoulders, one risk

A large risk is often too big for one insurer. **Subscription** means several insurers each
take a percentage of the same risk under the same terms. The shares add to 100%; the lead
usually takes the first line and sets the terms. If the risk is not fully subscribed, the
insured is not fully covered.

```
risk 100%
 ├── lead syndicate        50%
 ├── following syndicate A 30%
 └── following syndicate B 20%
                            ───
                           100%
```

In r-sure, each subscription is a `LineGrant` tied to the slip. At bind, each line becomes
a `Line` with credit, pay and release capabilities. The lines sum to 10000 basis points
(100.00%).

## 6. Claims: from notice to payment

A claim usually follows this path:

1. **Notice** (first notification of loss, FNOL) — the insured tells the insurer or broker.
2. **Coverage check** — is the loss within the period, the perils, the limits and the
   conditions?
3. **Adjustment** — an adjuster or the lead underwriter investigates, quantifies the loss
   and recommends an amount.
4. **Agreement** — the insurer(s) agree the amount. In a subscription market, the lead may
   bind the following market for standard claims; complex claims need a wider agreement.
5. **Settlement** — each insurer pays its share, less the deductible, within the limits.
6. **Recovery / subrogation** — the insurer may recover from a third party. r-sure does not
   implement subrogation.

A claim is not a payment request; it is an **adjudicated** request. The evidence, the
coverage analysis and the agreement matter as much as the bank transfer.

r-sure's `Claim` records classification, assessment, agreement, optional r-gen adjudication
and settlement. The `Policy` computes the payable amount and each `Line` pays its share.

## 7. Brokers, syndicates and reinsurance

- **Broker** — an intermediary who acts for the insured, prepares the submission, negotiates
  with underwriters and often handles claims. The broker is usually paid by commission.
- **Syndicate** — a group of capital providers that underwrites as one risk carrier. A
  managing agent operates the syndicate and employs the underwriters.
- **Reinsurance** — insurance for insurers. The insurer cedes part of its risk to a
  reinsurer, either proportionally (a share of every loss) or non-proportionally (losses
  above a retention). Reinsurance protects the insurer's capital and lets it write more
  business. r-sure does not implement reinsurance in v1; the term is defined here because
  Lloyd's is often described as a market with a reinsurance layer.

## 8. Capital and solvency

An insurer must hold capital against the possibility that claims are worse than expected.
The capital is the buffer that makes the promise credible. In Lloyd's, the buffer is layered:
syndicate assets, members' funds at Lloyd's, central assets and the Central Fund. r-sure
models the first layer as a syndicate-owned claims purse and the last as `SureFund`; the
middle layers are out of scope.

```
policyholder claim
      │
      ▼
syndicate claims purse  (capital + premium)
      │ shortfall
      ▼
central fund            (levy + administered cover)
```

## 9. The r-sure object map

| Insurance idea | r-sure object | What it does |
|---|---|---|
| Risk submission | `Risk` | asset, period, limits, evidence, insurability tri-test |
| Underwriting record | `Risk.assessment` | score/quote/credential reference (advisory) |
| Broker | `Broker` | registered intermediary and commission cap |
| Syndicate | `Syndicate` | capital, appetite, capacity, claims purse |
| Subscription | `LineGrant` / `Line` | reserved share, then written line |
| Placing slip | `Slip` | terms, subscriptions, premium, acceptance, bind |
| Policy | `Policy` | lines, premium distribution, aggregate, claims |
| Claim | `Claim` | notice, classify, assess, agree, dispute, settle |
| Premium | premium purse + `Distribution` | commission, levy, line credits |
| Deductible / limits | `CoverTerms`, `Policy.payable` | payable formula |
| Central fund | `SureFund` | levy and capped, administered shortfall cover |
| Evidence | `Risk.evidence`, `Claim.evidence` | r-gen hashes and URIs |

## 10. A worked example

An engineering project is insured for a 12-month period:

- aggregate limit: 1,000,000;
- per-claim limit: 400,000;
- deductible: 20,000;
- premium: 50,000;
- broker commission: 10%; central fund levy: 2.5%.

Two syndicates subscribe 60/40. A covered loss is agreed at 300,000.

```
payable = min(300,000, 400,000, 1,000,000) - 20,000
        = 280,000
syndicate A (60%) = 168,000
syndicate B (40%) = 112,000
```

The premium splits into 5,000 commission, 1,250 levy and 43,750 net for the lines. The
aggregate remaining after the claim is 720,000. These are the arithmetic invariants the
contracts are meant to enforce; the audit checks whether they actually do.

> **What this chapter is not.** It is a teaching simplification. Real policies have
> exclusions, warranties, conditions, reinstatement, subrogation, co-insurance, run-off and
> regulatory capital rules that r-sure does not model. Do not use it as a legal or
> compliance guide.
