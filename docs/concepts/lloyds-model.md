# The Lloyd's model

> **Status:** Implemented (source + static/parser gates). For the lay explanation, read
> [Lloyd's of London for dummies](../primer/lloyds-for-dummies.md).

Lloyd's is a marketplace, not an insurer. Members provide capital to **syndicates**; a
**managing agent** runs each syndicate; **brokers** place risks; the first syndicate to
subscribe is the **lead**, and the rest are **following** syndicates. Together they subscribe
to a **placing slip** (today usually a Market Reform Contract, MRC). The lead manages
standard claims; complex claims use the lead and a second syndicate. Claims are paid by each
syndicate in proportion to its line.

## The participants

- **Members** — the capital providers. Historically individual "Names"; today mostly
  corporate members and limited partnerships. They bear the syndicate's risk.
- **Syndicates** — the risk carriers. Each has its own appetite, plan, capital and claims.
- **Managing agents** — the companies that run syndicates, employ underwriters and manage
  claims. The managing agent is the underwriting authority.
- **Brokers** — the insured's representatives. They prepare the submission, negotiate terms,
  place the slip and usually handle claims.
- **The Corporation of Lloyd's** — the market's oversight and infrastructure body, not the
  insurer.

## Placing and subscription

The broker prepares the slip with the risk, coverage, limits, deductible, premium,
conditions and claims basis. The lead underwriter negotiates the terms and takes the first
line. Following underwriters accept shares on the same terms until the risk is 100%
subscribed. If the shares do not reach 100%, the risk is not fully placed.

```
broker -> lead (terms + first line) -> followers (same terms) -> 100%
```

## Claims

The broker notifies the lead managing agent. The lead acknowledges, checks the slip,
classifies the claim (standard or complex), informs the followers, investigates and
determines the claim. For a standard claim the lead's determination binds the following
market; for a complex claim the lead and second syndicate share the determination. The
broker remains the insured's advocate and passes the adjuster's report to underwriters.

## Central fund and chain of security

A Lloyd's policy is backed by a layered chain: syndicate assets, members' funds at Lloyd's,
central assets, and finally the Central Fund. The Central Fund is a governed, last-resort
protection arrangement, not an automatic guarantee. r-sure models the first layer as the
syndicate claims purse and the last as `SureFund`; the middle layers are out of scope.

## Mapping to r-sure

| Lloyd's | r-sure |
|---|---|
| Member capital | `Syndicate.contribute` into a contract-owned claims purse |
| Managing agent | the syndicate owner / `managerId` |
| Broker | `Broker`, registered with a licence hash and commission cap |
| Placing slip / MRC | `Slip` with `LineGrant` subscriptions |
| Lead / following | first subscriber / remaining subscribers |
| Policy | `Policy`, one per bound slip |
| Standard claim | lead classifies and agrees; followers are bound |
| Complex claim | lead + second manager must agree |
| Claims agreement | `Claim.agree` / optional r-gen `OracleCase` |
| Central fund | `SureFund`, levy-funded and administered |
| Chain of security | capital + premiums in the syndicate purse, then the fund |

The model is intentionally narrow. Reinsurance, coverholders, delegated authority,
endorsements and renewals are out of scope for v1. See the
[claims chapter](claims-and-adjudication.md) and [settlement chapter](settlement.md) for the
on-chain mechanics.
