# Project status

> **Status:** Contracts and formal model implemented; the audit and behavioural test campaign
> are in progress. This page is the single status summary for the repository.

## At a glance

| Area | Current state |
|---|---|
| Contracts | 17 deploy terms, 30 catalogue components and 19 state cells; static, parser and size gates pass. |
| Formal model | 108 Lean theorems over the insurance economics; 33 vectors; 11 `proved-model` flow rules; claims register 13 covered, 1 partial, 1 deferred, 1 tool. |
| Audit | 21 findings, 27 hazards and 21 improvements. P0/P1 source fixes are in; F-013 and F-015 are fixed; F-014, F-017 and F-018 are accepted boundaries. |
| Tests | 36 suites are registered. They are still being implemented; none is recorded as passing. |
| Devnet | The r-cash rail bootstraps, but the full r-sure install is blocked by a latent Slip name-binding defect and a node proposer continuation failure. |
| Documentation | mdBook under `docs/`; build with `make docs-check`. |

## Current blockers

- **Slip install.** The Slip bundle now closes statically (`bundle-closedness` reports no
  captured state), but deploying the term exposes a name/data binding defect in
  `SlipFactory` (`brand`/`issuer` are data-bound and used as names) and the devnet proposer
  fails with `decode continuation failed` after several bundled contracts are deployed.
  The full install and behavioural campaign must wait for those to be resolved.
- **Test campaign.** All 36 suite files are still templates that exit `not_run`. The insurance
  fixture, admin-signature helper, fault injection and devnet bring-up are the next
  implementation work.
- **Audit evidence.** F-002 is fixed at the bundle/static level; its E2 install reproduction
  is blocked by the Slip install issue above. Dynamic evidence remains `not_run`.

## What the formal model establishes

The Lean model proves capacity, subscription, premium allocation, payable bounds, settlement
conservation, exactly-once guards, terminal claim states, the central fund and the linear
cell. It is a shallow component model, not a refinement of the Rholang contracts. See
[Formal model](../reference/formal-model.md), [Proof map](../reference/proof-map.md) and
[Invariants](../reference/invariants.md).

## How to verify

```sh
make check          # static, parser and docs gates
make formal-check   # Lean, vectors, flows and claims
make audit-check    # registers, traceability, concurrency, interfaces, guards and pause
make unit-all       # behavioural suites when the devnet install is green
```

The detailed gate list and honesty rule are in [Verification](../reference/verification.md).

## Audit and test records

- [Audit report](https://github.com/rhovision-org/r-sure/blob/main/audit/report.md)
- [Findings register](https://github.com/rhovision-org/r-sure/blob/main/audit/registers/findings.yaml)
- [Hazards register](https://github.com/rhovision-org/r-sure/blob/main/audit/registers/hazards.yaml)
- [Improvements register](https://github.com/rhovision-org/r-sure/blob/main/audit/registers/improvements.yaml)
- [Test register](https://github.com/rhovision-org/r-sure/blob/main/audit/registers/tests.yaml)
- [Theorem register](https://github.com/rhovision-org/r-sure/blob/main/audit/registers/theorems.yaml)
- [Concurrency reviews](https://github.com/rhovision-org/r-sure/tree/main/audit/concurrency)
- [Composition interfaces](https://github.com/rhovision-org/r-sure/blob/main/audit/composition/interfaces.yaml)

## Next milestones

1. Resolve the Slip name/data binding and complete `make install`.
2. Implement the harness fixture and the 36 suites; run the campaign and record honest
   pass/fail/not_run.
3. Close the remaining audit evidence for F-002 and the accepted boundaries.
4. Re-run `make check formal-check audit-check docs-check`.
