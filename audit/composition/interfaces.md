# Interface matrix

> **Status:** Internal desk review, 2026-11-05.

The canonical rows are in [`interfaces.yaml`](interfaces.yaml). This page is the readable
summary.

| ID | Caller | Callee / arm | Success shape | Refusal shape | Verdict |
|---|---|---|---|---|---|
| C-01 | all terms | SureRoot.resolve | `(true, uri, version)` | `(false, reason, key?)` | safe |
| C-02 | AdminGuard | Codec/crypto | `(true, bool)` | `(false, below threshold)` | safe |
| C-03 | SureAdmin | AdminGuard.verify | `(true, bool)` | `(false, below threshold)` | concern |
| C-04 | Payments | r-cash Root.resolve | `(true, uri, version)` | `(false, reason, key)` | concern |
| C-05 | Payments | AssetResolver.issuer | `(true, brand, issuer)` | `(false, reason)` | concern |
| C-06 | Payments | AccountFactory/Account | `(true, account, ownerId)` / `(true, facet)` | `(false, reason)` | concern |
| C-07 | RgenAdapter | r-gen factories | `(true, uri, version)` / `(true, record)` | `(false, rgen unavailable)` | concern |
| C-08 | Syndicate | Payments.issuer | `(true, brand, issuer)` | `(false, reason)` | finding |
| C-09 | Syndicate.openLine | LineGrant.consume | `(true, quote)` | `(false, closed/not holder)` | finding |
| C-10 | Syndicate.openLine | LineFactory.create | `(true, lineUri)` | `(false, reason)` | finding |
| C-11 | SyndicateBook | makePurse | `(true, purse, brand, issuer)` | `(false, reason)` | concern |
| C-12 | BrokerBook | brokerMake/registerDone | `(true, id, uri)` | `(false, reason)` | finding |
| C-13 | RiskBook | riskMake | `(true, id, uri)` | `(false, reason)` | concern |
| C-14 | Slip.subscribe | Syndicate.quote | `(true, grantId, grantUri)` | `(false, reason)` | finding |
| C-15 | Slip.bind | Syndicate.openLine | `(true, lineId, lineUri)` | `(false, reason)` | finding |
| C-16 | Slip.bind | PolicyFactory.create | `(true, policyUri)` | `(false, reason)` | finding |
| C-17 | Slip.bind | Policy.distribute | `(true, Nil)` | `(false, not holder)` | finding |
| C-18 | Policy | SureMath | `(true, amounts)` | `(false, bps/shares/amount)` | concern |
| C-19 | Policy | Distribution | `(true, distUri/payments)` | `(false, reason)` | finding |
| C-20 | Policy | SureFund.covered | `(true, cover)` | `(false, not covered)` | concern |
| C-21 | Policy.openClaim | ClaimFactory.create | `(true, claimId, claimUri)` | `(false, reason)` | finding |
| C-22 | Claim.settle | Policy.settleClaim | `(true, payable)` | `(false, reason)` | finding |
| C-23 | Claim.dispute | RgenAdapter/OracleFactory | `(true, case)` | `(false, rgen unavailable)` | finding |
| C-24 | Distribution | Payments/SureFund/Line | `(true, _)` | `(false, reason)` | finding |
| C-25 | Line | Syndicate capabilities | `(true, amount)` | `(false, not holder)` | finding |
| C-26 | Books | Policy/Claim.info | `(true, state)` | `(false, reason)` | concern |
| C-27 | r-share | Distribution/Line/Policy | `(true, payments/payable)` | `(false, reason)` | concern |
| C-28 | all terms | Clock.now | `(true, height)` | `(false, clock unavailable)` | safe |
| C-29 | SureFund | Payments | `(true, brand, issuer)` / `(true, facet)` | `(false, reason)` | finding |
| C-30 | Claim.classify/assess | Policy.info | `(true, state)` | `(false, reason)` | concern |

## Reading the verdicts

- **safe** — no state held, reply shape understood, failure is a clean refusal.
- **concern** — a read-only boundary or a stale-peek risk; no confirmed P0/P1.
- **finding** — a confirmed issue in `../registers/findings.yaml` (double-consume, unclosed
  bundle, missing authorization/glue, or value-move ordering).

The three-guard exactly-once invariant is **not** a single map in the code:
`Line.paidFor`, `Policy.claims[claimId].status`, `Claim.status` and `SureFund.covers` are
four independent records. The review treats the claim token plus the claimId as the only
cross-component binding; it does not prove they refer to the same policy. That is a finding,
not an assumption of safety.
