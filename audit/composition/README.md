# Composition review

> **Status:** Internal desk review, 2026-11-05. Not an independent audit. Dynamic evidence is
> `not_run` until the devnet install clears the P0 bundle defect.

`interfaces.yaml` is the normative caller→callee table; `interfaces.md` is the readable
matrix. `../composition/reply-shapes.md` is a generated inventory of call sites and nearby
`match` patterns.

For every interface the review records:

- the call site and the request shape;
- the assumed success reply and refusal reply;
- whether the caller holds a state cell across the await;
- whether the call is read-only or value-moving;
- the capability/name flow;
- the failure behavior (graceful refusal, hang, or `1/0`);
- the cross-component invariant it enforces;
- a verdict and hazard/finding links.

The gate `tools/check_composition_audit.py` fails if a required interface is missing, a row
is incomplete, or a hazard/finding ID does not resolve.

## Cross-component invariants that are assumed, not checked

1. **r-cash reply shapes** — `(true, brand, issuer)`, `(true, facet)`, `(true, _)` are
   assumed. A changed shape either falls into a refusal or a `1/0` value-move rollback.
2. **r-gen reply shapes** — `OracleFactory.open` returns `(true, case)` and `OracleCase`
   calls `applyDecision`; a changed shape leaves the claim in `disputed`.
3. **Exactly-once settlement** is split across `Line.paidFor`, `Policy.claims[claimId]`,
   `Claim.status` and `SureFund.covers`. There is no check that a `claimId` passed to
   `Line.pay` belongs to the paying policy; the policy/claim tokens are the authority.
4. **termsHash** is computed at slip creation and is not revalidated at bind.
5. **Pause** is written by `SureAdmin` but no mutating arm consults it; the pause-scope
   invariant is currently vacuous.
6. **Books** are registered but never populated by the policy/claim factories.

These are recorded as findings/hazards, not assumed safe.
