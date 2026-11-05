# Verification

> **Status:** Static and parser gates run; behavioural, formal and client gates are scaffolded.

## Static and parser gates

```sh
make build-check      # no drift in contracts/build
make measure-check    # every term <= 56 KiB
make spec-check       # arch, captures, select, placeholders, money, suites
make parse-check      # target node parser on built and rendered terms
```

Recorded locally: 17 terms parse; 30 components; 19 state cells; acyclic; all terms within
budget; 162 source arms registered; 2 Lean theorems and 2 vectors; 8 flow rules still `owed`.
The Rust core, keystore, SDK, CLI and WASM crates compile; `cargo test --workspace` passes 6
tests (3 core arithmetic, 3 keystore). The web scaffold is not installed or built here.

## Audit gates (2026-11-05)

`make audit-check` now also enforces a concurrency review per component and a composition row
per interface, with no unresolved register IDs. `make audit-scan` runs the heuristic scanners
for unclosed bundles, take-await-take, reply shapes and pause scope.

Current audit state: 30/30 component reviews, 42 interfaces, 25 hazards, 19 findings, 19
improvements, 36 registered suites (`not_run`). The P0 take-await-take finding is fixed; the
P0 instance-bundle finding is open, so `make audit-scan` reports nine bundle candidates and
the devnet install remains blocked. The tabletop HAZOP is an internal simulation, not an
independent audit. See `audit/report.md`.

## Behavioural, formal and client gates

```sh
make unit-all         # honest pass/fail/not-run
make formal-check     # Lean, vectors, flows
make audit-check      # registers, arm inventory, traceability
make client-check     # Rust fmt/clippy/tests/wasm
make web-test web-build
```

The suite inventory is in `harness/run_suites.py`. A suite that has not been run must report
`not_run`, not `pass`. The audit evidence directory holds campaign snapshots.

## Honesty rule

"Implemented" means the source plus the static/parser gates. It does not mean the behaviour
has been verified on a devnet. "Tested" requires a named suite with a passing result.
