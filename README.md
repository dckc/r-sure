# r-sure — open insurance market rules for rholo

## What is r-sure, in plain language

r-sure is a set of open-source building blocks for running an insurance market on a
blockchain. It is modelled on how Lloyd's of London works: a group of backers (called
**syndicates**) put up capital, a **broker** places a risk for a customer, several backers
share that risk, and the resulting **policy** pays out if a covered loss happens.

The code covers the whole insurance journey:

- backers join a syndicate and reserve capacity;
- a broker prepares a placing slip and the customer accepts it;
- syndicates subscribe for a share of the risk;
- the policy collects the premium and splits it between the broker, a central fund and the
  syndicates;
- a claim is reported, assessed and agreed, and each syndicate pays its share exactly once;
- an optional independent evidence service can decide disputed engineering claims.

It is designed to work with three sibling projects:

- [r-cash](https://github.com/rhovision-org/r-cash) handles deposits and payments;
- [r-gen](https://github.com/rhovision-org/r-gen) supplies engineering evidence, credentials
  and dispute decisions;
- [r-share](https://github.com/rhovision-org/r-share) can reuse r-sure's payment and policy
  pieces for rentals and other cash-flow products.

## Summary

| Question | Answer |
|---|---|
| **What is it?** | Open-source insurance primitives written in Rholang for the rholo stack. |
| **Who is it for?** | Developers, researchers and auditors exploring on-chain insurance. |
| **What does it cover?** | Syndicate capital, broker placing, subscriptions, policies, premiums, claims and settlement. |
| **How is it built?** | Rholang contracts, a Rust client stack, a React web client, a Python devnet harness, a Lean model and an mdBook. |
| **Where do I start?** | [Insurance basics](docs/primer/insurance-basics.md), then [Lloyd's for dummies](docs/primer/lloyds-for-dummies.md), then the [design philosophy](docs/primer/design-philosophy.md). |

The repository follows the conventions of r-gen, r-share and r-cash: Rholang contracts with
one state cell per object, a Rust client stack, a Python devnet harness, a Lean model and an
mdBook.

## What is here

| Area | Path |
|---|---|
| Contracts | `contracts/src/deploy`, `contracts/src/lib`, `contracts/build` |
| Rust workspace | `crates/rsure-core`, `rsure-keystore`, `rsure-sdk`, `rsure-cli`, `rsure-wasm` |
| Web client | `web/` |
| Devnet harness | `harness/` |
| Tools and checks | `tools/` |
| Spec, flows and Lean | `spec/` |
| Book | `docs/` |

## Core primitives

- **SureRoot** — installer-gated component directory with 2-of-3 governance.
- **SyndicateBook / Syndicate / LineGrant** — capital, capacity, quotes and one-shot
  capacity reservations. A syndicate's claims purse is contract-owned.
- **BrokerBook / Broker** — registered intermediary with a licence hash and commission cap.
- **RiskBook / Risk** — the insured's submission, the three insurability questions and
  r-gen evidence references.
- **SlipFactory / Slip** — a placing slip: insured acceptance, lead/follow subscriptions,
  premium funding and binding.
- **LineFactory / Line** — one policy-syndicate share, holding the credit, pay and release
  capabilities in closure.
- **PolicyFactory / Policy** — the bound policy, premium distribution and aggregate limit.
- **ClaimFactory / Claim** — FNOL, classification, assessment, lead/second agreement,
  r-gen OracleCase adjudication and settlement.
- **DistributionFactory / Distribution** — an exactly-once account/fund/line waterfall,
  reusable by r-share for revenue splits and staged payments.
- **SureFund** — central fund levies and 2-of-3-gated, capped shortfall cover.
- **PolicyBook / ClaimBook** — discovery indexes.

## Integrations

- **r-cash**: premiums are funded from an r-cash account into a policy-owned purse; claim
  payouts and refunds go to r-cash deposit facets. The Payments adapter is resolved per arm.
- **r-gen**: risk and claim evidence carry r-gen claim/validation/K-Asset/provenance URIs.
  A disputed claim opens an r-gen `OracleCase`; the credential-proved adjudicator decides and
  executes into the claim's private `applyDecision` capability.
- **r-share**: `Distribution`, `Line` and `Policy` are the reusable interfaces. A booking
  damage waiver can layer an r-sure policy above r-share's deposit/escrow flow. r-share is not
  modified by this repository.

## Documentation

The book in `docs/` covers the insurance primer, the Lloyd's model, placement, binding,
claims and the contract reference. Developer notes are in `AGENTS.md`.

## License

AGPL-3.0-only. See `LICENSE` and `THIRD_PARTY_NOTICES.md`.
