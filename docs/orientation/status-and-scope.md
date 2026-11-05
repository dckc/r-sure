# Status and scope

> **Status:** Implemented (source + static/parser gates). Behavioural suites are scaffolded
> and mostly report `not_run`.

## What is implemented

- 17 deploy terms, 30 catalogue components, 19 state cells.
- The kernel, admin multisig, coverage terms, integer math, r-cash adapter and optional
  r-gen adapter.
- Syndicates, brokers, risks, slips, lines, policies, claims, distribution and the central
  fund.
- Static gates: build drift, size, architecture, captures, no-select, placeholders, integer
  money, suite inventory, parser.
- mdBook, specification skeletons, audit registers and the Rust/web scaffolds.

## What is not implemented or not yet verified

- The devnet campaigns. Most `unit_*` suites exit 2 (`not_run`) until the campaign is run.
- The Lean model is scaffolded; the proofs and flow manifest are not complete.
- The Rust client, CLI, WASM and web app are scaffolds; they are not built or tested here.
- Endorsements, renewals, reinstatement, reinsurance, delegated underwriting, premium
  instalment schedules, subrogation, salvage and FX at claim time are out of scope for v1.
- No KYC/AML, fiat rails, regulatory reporting, mainnet deployment or real value.

## Trust boundary

- r-cash owns the accounts and the settlement rail.
- r-gen owns engineering claims, validations, K-Assets, credentials and adjudication.
- r-sure owns the insurance market: capacity, placing, policies, claims and the central fund.
- r-share is a consumer of the reusable `Distribution` / `Line` / `Policy` interfaces; this
  repository does not modify r-share.
