# Lloyd's of London for dummies

> **Status:** Primer (stable). A simplification for software readers, not a legal or
> regulatory description of Lloyd's.

Lloyd's of London is not an insurance company. It is a **marketplace** and a **corporate
umbrella** under which independent **syndicates** accept risk. The policyholder deals with
the market through a **broker**; the broker deals with syndicates through a **placing slip**;
the syndicates share the risk and pay claims in proportion to their shares. The Corporation
of Lloyd's sets the rules, provides the infrastructure and protects the market's reputation.

This chapter explains the parts r-sure models and the parts it deliberately leaves out. The
[insurance basics](insurance-basics.md) chapter defines the underlying terms.

## 1. The cast

```
                    Corporation of Lloyd's
                    (market rules, oversight)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   members/Names       managing agents          brokers
   (capital)           (run syndicates)         (place risks)
        │                     │                     │
        └──────▶ syndicates ◀─┘                     │
                     ▲                              │
                     │ subscription                 │
                     └──────── placing slip ◀───────┘
                                     ▲
                                     │
                                  insured
```

- **Members** provide capital. Historically many were individual "Names"; today most capital
  comes from corporate members and limited partnerships. The members are the ultimate
  bearers of the syndicate's risk.
- **Syndicates** are the risk carriers. A syndicate is formed by one or more members; it has
  its own underwriting plan, risk appetite, capital and claims. Syndicates are technically
  annual but operate year to year.
- **Managing agents** run the syndicates. They employ the underwriters, set the underwriting
  plan, manage claims and provide the infrastructure. A managing agent may manage several
  syndicates.
- **Brokers** distribute the business. Lloyd's is a broker market: the broker acts for the
  insured, prepares the submission, negotiates with underwriters and usually handles claims.
- **Coverholders** are third parties authorised by a managing agent to accept risks on its
  behalf in a territory. They are common in delegated-authority business. r-sure does not
  model them.
- **The Corporation of Lloyd's** is not the insurer. It oversees the market, maintains the
  central fund and provides services.

## 2. Placing a risk: the slip and the subscription

The broker prepares a **placing slip**. The modern form is the **Market Reform Contract
(MRC)**, but the market still calls it the slip. The slip contains:

- the insured and the period;
- the risk description and the asset or project;
- coverage, limits, deductibles and exclusions;
- the premium and commission;
- the conditions and the claims basis;
- the shares taken by each syndicate.

The broker takes the slip to a **lead** underwriter. The lead negotiates the terms and
accepts a line — the first share. The slip then goes to **following** underwriters, who
accept smaller shares on the same terms. When the shares reach 100%, the risk is fully
placed. If a following underwriter wants a different term, the lead must agree; otherwise the
risk may be **signed down** or left partly unplaced.

```
broker ── slip ──▶ lead underwriter ── 50% ──▶ terms set
                         │
                         ├──▶ follower A ── 30%
                         └──▶ follower B ── 20%
                                            ───
                                           100%
```

The lead's role is not just administrative. The lead's underwriting work is what the
following market relies on; the lead also usually takes the larger share and manages the
claim.

r-sure models the slip as `Slip`, the lead as the first subscription, the following market as
the remaining `LineGrant`s, and the fully subscribed state as 10000 bps.

## 3. Claims at Lloyd's

When a loss happens, the broker notifies the lead syndicate's managing agent. The lead:

1. acknowledges the claim;
2. checks the slip and the evidence;
3. classifies the claim as **standard** or **complex**;
4. informs the following syndicates;
5. investigates and determines the claim.

For a **standard** claim, the lead's managing agent determines the claim on behalf of all the
Lloyd's syndicates on the slip. For a **complex** claim, the determination is shared between
the lead and a **second** syndicate. The claims agreement terms in the slip say which
arrangement applies. The market's electronic claims facilities (historically ECF, now
replaced by newer services) carry the documents; the principle is that the lead's agreement
binds the following market for standard claims.

```
insured ──▶ broker ──▶ lead managing agent
                         │  standard: lead agrees
                         │  complex: lead + second agree
                         ▼
                 each syndicate pays its share
```

The broker is the insured's advocate. In open-market business the broker receives the
adjuster's report and presents the claim to underwriters; it can head off disputes before a
formal reservation of rights or denial.

r-sure models this with `Claim.classify`, `Claim.assess`, `Claim.agree` and the optional
r-gen `OracleCase` for a disputed or complex decision. The standard/complex basis is a term
in the slip; the lead and second managers are taken from the policy lines.

## 4. Central fund and the chain of security

A policyholder at Lloyd's is protected by a layered chain of security:

1. **Syndicate assets** — the syndicate's premium, reserves and investments.
2. **Members' funds at Lloyd's** — capital posted by the members, held by the Corporation.
3. **Central assets** — assets held by the Corporation and the market.
4. **Central Fund** — the market's mutual fund, available at the discretion of the Council
   to meet a member's unpaid liabilities.

```
claim
  │
  ▼
syndicate assets ──▶ members' funds at Lloyd's ──▶ central assets ──▶ Central Fund
```

The Central Fund is not a conventional insurance policy. It is a last-resort protection
arrangement, governed by the market, not a guarantee that every claim is paid
automatically. r-sure models a simplified version: the syndicate claims purse is the first
layer; `SureFund` is a levy-funded, capped, one-shot cover that requires 2-of-3 signatures.
The middle layers are out of scope.

## 5. Why the market is structured this way

The structure solves several problems at once:

- **Capital** — many members can back a syndicate; the risk is spread.
- **Expertise** — managing agents specialise in classes of business.
- **Distribution** — brokers bring risks and represent the insured.
- **Peer review** — the lead's terms are visible to followers; a bad lead loses its
  following market.
- **Claims** — the lead manages the claim, so the insured deals with one decision-maker
  even though several syndicates carry the risk.
- **Security** — the chain of security and the Central Fund stand behind the syndicate.

The cost is complexity: many parties, documents, signatures, allocations and reconciliation.
That complexity is what a shared ledger and smart contracts can reduce — if the primitives
are correct.

## 6. What r-sure models, and what it does not

| Lloyd's concept | r-sure | Notes |
|---|---|---|
| Member capital | `Syndicate.capital` | contract-owned claims purse |
| Managing agent | syndicate owner/manager | owner-gated |
| Broker | `Broker` | licence hash, commission cap |
| Placing slip / MRC | `Slip` | terms, shares, premium, bind |
| Lead / following | first subscription / rest | manager-derived |
| Signing down | partial subscription | bind requires 10000 bps |
| Standard claim | lead agreement | `Claim.classify` / `agree` |
| Complex claim | lead + second agreement | `Claim.agree` quorum |
| Claims agreement | `Claim` + optional r-gen oracle | `applyDecision` |
| Premium | premium purse + `Distribution` | commission, levy, lines |
| Claims payment | `Line.pay` | pro rata from syndicate purses |
| Chain of security | syndicate purse + `SureFund` | middle layers out of scope |
| Reinsurance | not modelled | defined but out of scope |
| Coverholders / delegated authority | not modelled | out of scope |
| XCS / ECF | not modelled | no off-chain claims service |

## 7. A placement in one page

```
1. insured -> broker: submission, evidence, requested limits
2. broker -> lead: slip with terms and premium
3. lead -> slip: subscribe 50% (LineGrant)
4. followers -> slip: subscribe 30% + 20%
5. insured -> slip: accept terms, fund premium
6. anyone -> slip: bind (10000 bps, premium funded)
7. slip -> lines + policy + premium distribution
8. loss -> broker -> lead: claim notice + evidence
9. lead -> claim: classify, assess; standard = lead, complex = lead+second
10. claim -> policy -> lines: settle pro rata to the insured
```

r-sure's contracts implement this sequence as a set of capability-gated objects. The
[subscription market](../concepts/subscription-market.md), [claims and
adjudication](../concepts/claims-and-adjudication.md) and [settlement](../concepts/settlement.md)
chapters give the on-chain detail.

> **What this chapter is not.** Lloyd's is a regulated market with rules, capital
> requirements, delegated authority, sanctions, disputes and a long legal history. This is a
> software-oriented simplification. r-sure is not affiliated with Lloyd's and does not
> reproduce its legal structure.
