# Evidence and r-gen

> **Status:** Implemented (source + static/parser gates); r-gen cross-checks are optional.

Only hashes and references go on-chain. A risk carries an asset reference, the three
insurability questions and a list of evidence references:

```json
{"kind": "rgen:kasset", "uri": "rho:id:...", "hash": "<hex>"}
```

Allowed kinds include `rgen:identity`, `rgen:credential`, `rgen:claim`, `rgen:validation`,
`rgen:kasset`, `rgen:provenance`, `rgen:oracle-case`, `external:report` and
`external:document`.

A risk may also carry a **variance attestation**:
`{source:"attested", kassetUri, varianceBps, evidenceHash}`. It must match an `rgen:kasset`
evidence entry, and the source is recorded. The engineering estimate is derived from the
K-Asset when no attestation is supplied; the insurer's estimate is recorded separately and
the signed gap is visible.

`RgenAdapter` stores the optional r-gen Root and factory URIs. When enabled it can verify a
credential or a claim through the r-gen factory `verify` arms, and a provenance URI through
`Provenance.verify`. It is disabled by default; insurance does not require r-gen to place a
risk or settle a claim.

## Adjudication

An r-gen `OracleCase` has one credential-proved adjudicator. r-sure's `Claim.dispute` calls
`OracleFactory.open(..., caseReq, applyCap)` with the claim's private `applyDecision`
capability. The adjudicator decides and executes; the case calls `applyDecision`, which maps
the outcome to the claim's agreed amount. The capability is one-shot and bound to the claim,
so a decision cannot be applied to another claim.
