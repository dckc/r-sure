# Verification

> **Status:** Static, parser, Lean, audit, behavioural and web gates run and pass locally.
> The Lean model is a shallow component model, not a Rholang refinement.

## Static and parser gates

```sh
make build-check      # no drift in contracts/build
make measure-check    # every term <= 56 KiB
make normalize-check  # every rendered term normalizes through the rholo parser
make spec-check       # arch, captures, select, placeholders, money, suites
make parse-check      # target node parser on built and rendered terms
```

Recorded locally: 17 terms parse; 30 components; 19 state cells; acyclic; all terms within
budget; 162 source arms registered; 261 Lean theorems, 33 vectors and 51 flow rules with 11
`proved-model` core arms. The claims register reports 24 covered, 1 partial and 1 tool entry,
with 161 substantive theorems, 1 weak and no unaudited theorem. The Rust core, keystore, SDK,
CLI and WASM crates compile; `cargo test --workspace` passes 10 tests (5 core, 3 keystore,
2 SDK). The web app typechecks, runs 7 Vitest tests, lints with no errors and builds; the
Playwright journeys pass against the installed devnet.

## Audit gates (2026-11-05)

`make audit-check` enforces a concurrency review per component, a composition row per
interface, the F-020/F-021 guard checks and the narrow pause scope, with no unresolved
register IDs. `make audit-scan` runs the heuristic scanners for unclosed bundles,
take-await-take, reply shapes and pause scope.

Current audit state: 30/30 component reviews, 42 interfaces, 35 hazards, 25 findings (22
fixed, 3 accepted boundaries), 25 improvements, 39 registered suites and 261 registered
theorems. `check_bundle_closedness.py` reports zero candidates. The devnet install completes
all 17 terms and the node proposes blocks; the install root-cause analysis is recorded under
`audit/evidence/2026-11-05-install-rca`. F-003 (narrow, fail-closed pause), F-020 (payable
minimum and aggregate guard) and F-021 (terminal claim guards) are fixed; INV-9 and INV-10
are covered, and INV-12 is a source-gated tool check. The tabletop HAZOP is an internal
simulation, not an independent audit. See `audit/report.md`.

## Behavioural, formal and client gates

```sh
make unit-all         # honest pass/fail/not-run
make formal-check     # Lean build, axioms, vectors, flows, claims, critical path
make audit-check      # registers, traceability, concurrency, interfaces, guards and pause scope
make client-check     # Rust fmt/clippy/tests/wasm
make web-lint web-test web-build
make web-e2e          # Playwright, devnet-gated
```

The behavioural campaign's current output is recorded in `deployments/suite-results.json`:
37 runs, 375 assertions, 0 assertion failures. The coverage report derives 36/39 registered
suites passing (three `not_run` process gates), 120/145 public arms, 133/162 all registered
arms and 8/11 core-flow arms asserted.

The formal gate's current output:

```text
lean: built, 261 axiom audits, 261 source theorems, no sorry/admit/axiom/native_decide
vectors: 33 vectors current
check-flows: 51 rules, 40 arms, 11 core arms proved-model, 0 proof-quality warnings
claims: covered=24, partial=1, deferred=0, tool=1, substantive=161, weak=1, unaudited=0
check-critical-path: 14 critical primitives covered, arms/flows/suites/hazards joined
```

The suite inventory is in `harness/run_suites.py`. A suite that has not been run must report
`not_run`, not `pass`. The audit evidence directory holds campaign snapshots.

## Honesty rule

"Implemented" means the source plus the static/parser gates and, where stated, a passing
devnet campaign. "Tested" requires a named suite with a passing result. The Lean model is
`proved-model`: it is proved about a shallow state model, not refined to the Rholang terms.
