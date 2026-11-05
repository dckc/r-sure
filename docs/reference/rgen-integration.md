# r-gen integration

> **Status:** Implemented (contract interface); the devnet integration suite is scaffolded.

r-sure does not link r-gen Rust crates. It speaks the Rholang interface and defines minimal
wire types in `rsure-core`.

## Evidence

`RgenAdapter` resolves these r-gen components from the configured r-gen Root:

- `component:oracle-factory`
- `component:credential-factory`
- `component:claim-factory`
- `component:provenance-factory`

Reads: `verifyCredential(uri)`, `verifyClaim(uri)`, `verifyProvenance(uri, hash)`.
`health` reports the resolved versions; `config` returns the adapter state.

## OracleCase

`Claim.dispute(dId, caseReq)` resolves `component:oracle-factory` and calls:

```rholang
OracleFactory!("open", *dId, claimUri, caseReq, *ClaimApply, *ret)
```

`ClaimApply(@"applyDecision", caseId, decision, ret)` is private to the claim. The r-gen
`OracleCase.execute` calls it once. Outcomes map to `upheld`, `partially_upheld` or `denied`.
