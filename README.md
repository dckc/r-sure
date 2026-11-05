# r-sure — Lloyd's-style insurance primitives for rholo

**Devnet-only, unaudited, no real value. Not an insurer, not regulated, not affiliated with
Lloyd's of London.**

r-sure is a suite of Rholang smart-contract primitives for the Lloyd's subscription market:
syndicates with capacity, brokers, placing slips, lead and following subscriptions, policies,
premium allocation, standard and complex claims, and pro-rata settlement. It settles premiums
and payouts through [r-cash](https://github.com/rhovision-org/r-cash) (`~/Rholphin`) and
consumes engineering evidence and adjudication from
[r-gen](https://github.com/rhovision-org/r-gen) (`~/RGen`).

The repository is a sibling of r-gen, r-share and r-cash. It follows their conventions:
Rholang contracts with one state cell per object, a Rust client stack, a Python devnet
harness, a Lean model, audit registers and an mdBook.

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
| Lean model | 2 proved arithmetic theorems, 2 vectors, 8 owed flow rules |
| Audit | registers, HAZOP nodes and 3 hazards; 0 findings; no completed audit |

"Do not use real funds." The chain is pre-testnet and the contracts are unaudited.

### Known install blocker

A local devnet install reaches `16_fund.rho`; `10_syndicate.rho` is refused at deploy time
with `Bundle's content must not have free variables or wildcards`. The instance contracts
(`Syndicate`, `LineGrant`) capture their creation parameters, so the `bundle+{*…}` publication
needs the same refactor r-share uses for per-object contracts. Static build/measure/parse and
the Rust core/keystore tests pass; the devnet campaign is not green yet. This is recorded in
`audit/report.md`.

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
