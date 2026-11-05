# Verification

> **Status:** Static, parser, Lean and audit gates run; behavioural and client gates are
> scaffolded. The Lean model is a shallow component model, not a Rholang refinement.

## Static and parser gates

```sh
make build-check      # no drift in contracts/build
make measure-check    # every term <= 56 KiB
make spec-check       # arch, captures, select, placeholders, money, suites
make parse-check      # target node parser on built and rendered terms
```

Recorded locally: 17 terms parse; 30 components; 19 state cells; acyclic; all terms within
budget; 162 source arms registered; 108 Lean theorems, 33 vectors and 11 `proved-model` flow
rules. The claims register reports 13 covered, 1 partial, 1 deferred and 1 tool entry with 44
substantive theorems and no unaudited theorem. The Rust core, keystore, SDK, CLI and WASM
crates compile; `cargo test --workspace` passes 6 tests (3 core arithmetic, 3 keystore). The
web scaffold is not installed or built here.

## Audit gates (2026-11-05)

`make audit-check` now also enforces a concurrency review per component, a composition row
per interface, the F-020/F-021 guard checks and the narrow pause scope, with no unresolved
register IDs. `make audit-scan` runs the heuristic scanners
for unclosed bundles, take-await-take, reply shapes and pause scope.

Current audit state: 30/30 component reviews, 42 interfaces, 27 hazards, 21 findings, 21
improvements, 36 registered suites (`not_run`), and 108 registered theorems. The P0
take-await-take and instance-bundle findings are fixed in source; `check_bundle_closedness.py`
reports zero candidates. The devnet install is blocked by a SlipFactory name/data binding
defect and a node proposer continuation failure.
F-003 (narrow, fail-closed pause), F-020 (payable minimum and aggregate guard) and F-021
(terminal claim guards) are fixed; INV-9 and INV-10 are now covered, and INV-12 is a
source-gated tool check.
The tabletop HAZOP is an internal simulation, not an independent audit. See
`audit/report.md`.

## Behavioural, formal and client gates

```sh
make unit-all         # honest pass/fail/not-run
make formal-check     # Lean build, axioms, vectors, flows, claims
make audit-check      # registers, traceability, concurrency, interfaces, guards and pause scope
make client-check     # Rust fmt/clippy/tests/wasm
make web-test web-build
```

The formal gate's current output:

```text
lean: built, 108 axiom audits, 108 source theorems, no sorry/admit/axiom/native_decide
vectors: 33 vectors current
check-flows: 11 rules, 11 arms, 11 core arms proved-model, 0 proof-quality warnings
claims: covered=13, partial=1, deferred=1, tool=1, substantive=44, weak=1, unaudited=0
```

The suite inventory is in `harness/run_suites.py`. A suite that has not been run must report
`not_run`, not `pass`. The audit evidence directory holds campaign snapshots.

## Honesty rule

"Implemented" means the source plus the static/parser gates. It does not mean the behaviour
has been verified on a devnet. "Tested" requires a named suite with a passing result.
