# r-sure — open insurance market rules for rholo

> **Experimental, devnet-only, no real money.** r-sure is not an insurer, is not regulated,
> and is not affiliated with Lloyd's of London. The contracts are unaudited and the devnet
> install is still blocked by an open bundle defect.

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
| **What works today?** | Contracts, static/parser gates, Lean proofs of the core economics and internal audit registers. |
| **What is not ready?** | No production deployment, no real funds, no independent audit; the devnet install is still blocked by an open bundle defect. |
| **Where do I start?** | [Insurance basics](docs/primer/insurance-basics.md), then [Lloyd's for dummies](docs/primer/lloyds-for-dummies.md), then the [design philosophy](docs/primer/design-philosophy.md). |

The repository follows the conventions of r-gen, r-share and r-cash: Rholang contracts with
one state cell per object, a Rust client stack, a Python devnet harness, a Lean model, audit
registers and an mdBook.

## What is here

| Area | Path |
|---|---|
| Contracts | `contracts/src/deploy`, `contracts/src/lib`, `contracts/build` |
| Rust workspace | `crates/rsure-core`, `rsure-keystore`, `rsure-sdk`, `rsure-cli`, `rsure-wasm` |
| Web client | `web/` |
| Devnet harness | `harness/` |
| Static gates and tools | `tools/` |
| Spec, flows and Lean | `spec/` |
| Audit registers | `audit/` |
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

## Status

| Gate | State |
|---|---|
| Contracts build, measure, parse | 17 terms, 30 components, 19 state cells, all within the 56 KiB budget |
| Static gates | `make spec-check`, `parse-check`, `docs-check`, `formal-check`, `audit-check` green |
| Behavioural suites | 36 suites mapped; most are `not_run` until the devnet campaign |
| Rust client | core/keystore/sdk/cli/wasm crates compile; 6 unit tests pass; SDK/CLI are scaffolds |
| Web client | React/Vite scaffold; not installed or built here |
| Lean model | 108 kernel-checked theorems over a shallow component model; 33 vectors; 11 proved-model flow rules; claims register 13 covered, 1 partial, 1 deferred, 1 tool |
| Audit | 30/30 component concurrency reviews, 42 interfaces, 27 hazards, 21 findings; 1 of 2 P0s fixed; all 12 P1s fixed; tabletop HAZOP is internal |

"Do not use real funds." The chain is pre-testnet and the contracts are unaudited.

### Known install blocker

A local devnet install reaches `16_fund.rho`; `10_syndicate.rho` is refused at deploy time
with `Bundle's content must not have free variables or wildcards`. The 2026-11-05 audit found
nine affected instance types (`LineGrant`, `Syndicate`, `Line`, `Slip`, `Policy`, `Claim`,
`Distribution`, `Broker`, `Risk`), not just `Syndicate`/`LineGrant`. The fix is a closed
publication/init pattern; it is recorded as open finding F-002 in `audit/registers/findings.yaml`
and `audit/report.md`. The audit also fixed a P0 take-await-take defect in eight cornerstone
arms. Static build/measure/parse and the Rust core/keystore tests pass; the devnet campaign is
not green yet. The tabletop HAZOP is an internal simulation, not an independent audit.

## Integrations

- **r-cash**: premiums are funded from an r-cash account into a policy-owned purse; claim
  payouts and refunds go to r-cash deposit facets. The Payments adapter is resolved per arm.
- **r-gen**: risk and claim evidence carry r-gen claim/validation/K-Asset/provenance URIs.
  A disputed claim opens an r-gen `OracleCase`; the credential-proved adjudicator decides and
  executes into the claim's private `applyDecision` capability.
- **r-share**: `Distribution`, `Line` and `Policy` are the reusable interfaces. A booking
  damage waiver can layer an r-sure policy above r-share's deposit/escrow flow. r-share is not
  modified by this repository.

## Quickstart

```sh
make venv
make build-check measure-check spec-check parse-check
make devnet rcash-keys rcash-bootstrap keys install
make unit-all
```

See `docs/` for the book and `AGENTS.md` for the operating rules.

## License

AGPL-3.0-only. See `LICENSE` and `THIRD_PARTY_NOTICES.md`.
