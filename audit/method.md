# Audit method

1. **Static review** of every deploy term against the platform pitfalls in `AGENTS.md`.
2. **Architecture review** of `contracts/components.json`: state ownership, dependency
   acyclicity, capability placement.
3. **HAZOP** over the 15 nodes in `hazop/nodes.md`; each deviation becomes a hazard.
4. **Invariant review** against `spec/invariants.md`, including conservation, exactly-once,
   capacity and aggregate bounds.
5. **Behavioural campaign** on a fresh devnet: unit suites, races, refusals, idempotency,
   conservation, r-cash and r-gen integrations. Results are honest pass/fail/not-run.
6. **Formal review**: Lean model, vectors, flow manifest and axiom audit.
7. **Traceability**: every arm maps to hazards, findings, improvements, tests and Lean
   declarations where applicable.

Evidence lives in `audit/evidence/<date>/`.
