# Audit method

> **Status:** Internal method, 2026-11-05.

1. **Static review** of every deploy term against the platform pitfalls in `AGENTS.md`.
2. **Architecture review** of `contracts/components.json`: state ownership, dependency
   acyclicity, capability placement and cross-cell writers.
3. **Per-component concurrency review**: one row and one file per component in
   `concurrency/`. Each arm is classified with the Rholphin vocabulary (P1 take/validate/post,
   P2 peek/await/take/revalidate, P3 peek/effect/take/revalidate, P4 native-ERTP hold), and
   checked for second takes without a repost, peeks before awaits, `1/0` position, capability
   flow, bundle closedness and replay guards.
4. **Composition review**: one row per caller/callee interface in `composition/`, with the
   request, success/refusal reply, state held, atomicity and capability flow.
5. **HAZOP**: 15 nodes × 19 guide words × the node's parameters; the deviations are recorded
   in `registers/hazards.yaml`.
6. **Tabletop**: an internal simulation with chair/scribe/contracts/claims/cash/evidence/
   adversary/operations roles. It is not an independent facilitated HAZOP.
7. **Invariant review** against `spec/invariants.md`.
8. **Behavioural campaign** on a fresh devnet: 36 suites, honest pass/fail/not_run. Currently
   blocked by the P0 bundle defect.
9. **Formal review**: Lean model, vectors, flow manifest and axiom audit.
10. **Traceability**: every arm maps to hazards, findings, improvements, tests and Lean
    declarations where applicable.
11. **RCA**: for an install or liveness incident, record a fault tree with evidence at
    every leaf, five whys, hypotheses, experiments with artifacts, root cause, escape
    analysis, corrective actions, verification and residual risk in
    `audit/registers/rca.yaml` and `audit/evidence/<date>-<slug>/rca.md`.

Evidence lives in `audit/evidence/<date>/`. A finding is not "fixed" unless the change and
its regression (or a documented `not_run`) are in the tree.
