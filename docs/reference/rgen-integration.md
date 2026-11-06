# r-gen integration

> **Status:** Implemented (contract interface); the devnet integration suite passes,
> including a K-Asset stub for the variance read.

r-sure does not link r-gen Rust crates. It speaks the Rholang interface and defines minimal
wire types in `rsure-core`.

## Evidence

`RgenAdapter` resolves these r-gen components from the configured r-gen Root:

- `component:oracle-factory`
- `component:credential-factory`
- `component:claim-factory`
- `component:provenance-factory`

Reads: `verifyCredential(uri)`, `verifyClaim(uri)`, `verifyProvenance(uri, hash)` and
`variance(kassetUri)`. `health` reports the resolved versions; `config` returns the adapter
state.

## Variance is risk

`RgenAdapter("variance", kassetUri, ret)` is the primary interoperation. It reads the
K-Asset through the public `KAsset("get")` arm and returns
`(true, {source:"derived", kasset, varianceBps, quantity, qualitySum, verdict, status,
liabilityBps})`. The rate is `Var(value)/mean(value)^2` in bps; the derivation is in
[Variance is risk](../concepts/variance-is-risk.md).

The adapter validates the r-gen conventions itself, because the core passes them through
without shape checks:

- `quantity = {unit: non-empty string, value: integer ≥ 1}`;
- the four quality dimensions, each 1..5;
- `verdict` `valid` or `partial`; `invalid` is refused;
- `status == "approved"` with a non-nil `approval.liability.shareBps` in 0..10000.

`validated` and `conditional` have no liability record, so they refuse derivation with
`"approval"`; `disputed`, `upheld`, `revoked` and `partially_revoked` refuse with
`"status"`. A bound variance attestation on the risk submission is the fallback and records
`source:"attested"`. The adapter never writes to r-gen, never takes a capability, and does not
require the r-gen root: the K-Asset URI is read directly.

## OracleCase

`Claim.dispute(dId, caseReq)` resolves `component:oracle-factory` and calls:

```rholang
OracleFactory!("open", *dId, claimUri, caseReq, *ClaimApply, *ret)
```

`ClaimApply(@"applyDecision", caseId, decision, ret)` is private to the claim. The r-gen
`OracleCase.execute` calls it once. Outcomes map to `upheld`, `partially_upheld` or `denied`.
