# The Lloyd's model

> **Status:** Implemented (source + static/parser gates).

Lloyd's is a marketplace, not an insurer. Members provide capital to **syndicates**; a
**managing agent** runs each syndicate; **brokers** place risks; the first syndicate to
subscribe is the **lead**, and the rest are **following** syndicates. Together they subscribe
to a **placing slip**. The lead manages standard claims; complex claims use the lead and a
second syndicate. Claims are paid by each syndicate in proportion to its line.

r-sure expresses that structure on-chain:

| Lloyd's | r-sure |
|---|---|
| Member capital | `Syndicate.contribute` into a contract-owned claims purse |
| Managing agent | the syndicate owner / `managerId` |
| Broker | `Broker`, registered with a licence hash and commission cap |
| Placing slip | `Slip` with a list of `LineGrant` subscriptions |
| Lead / following | first subscriber / remaining subscribers |
| Policy | `Policy`, one per bound slip |
| Standard claim | lead manager classifies and agrees; followers are bound |
| Complex claim | lead + second manager must agree |
| Claims agreement | `Claim.agree` / optional r-gen `OracleCase` |
| Central fund | `SureFund`, levy-funded and administered |
| Chain of security | capital + premiums in the syndicate purse, then the fund |

The model is intentionally narrow. Reinsurance, coverholders and delegated authority are out
of scope for v1.
