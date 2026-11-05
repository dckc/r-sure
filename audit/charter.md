# Audit charter

> **Status:** Internal charter, 2026-11-05.

r-sure is a devnet-only research prototype. The audit is an internal, adversarial review of:

1. capacity and subscription integrity;
2. premium custody and distribution;
3. claim classification, agreement and settlement;
4. the optional r-gen evidence and adjudication path;
5. the r-cash payment boundary;
6. authority, replay, pause and liveness;
7. concurrency (state-cell take/repost, awaits, value moves);
8. composition (caller/callee reply shapes, cross-component invariants).

Out of scope: regulatory compliance, KYC/AML, fiat custody, mainnet deployment, real value,
r-gen internals, r-cash internals, and the Rust/web client behavior beyond the interface.

## Roles

Chair, scribe, contracts, claims, cash/r-cash, evidence/r-gen, adversary and operations. In
this pass the roles are an internal simulation, not an independent panel.

## Evidence standard

- E0 unverified — P3 only.
- E1 source reference (`file:line`) — all findings.
- E2 devnet reproduction — P0/P1 where possible.
- E3 machine-checked theorem.
- E4 proved-tied.

P0/P1 findings need E1 source evidence and a hazard; a fixed finding needs the change and a
regression (or a documented `not_run`).

## Exit criteria

- Every component has a concurrency review and every interface has a composition row.
- Every P0/P1 finding is fixed, or explicitly open with an owner and a proposed fix.
- The tabletop record is complete and labelled internal.
- No "audited" or production-safe claim without dynamic evidence and an independent review.
