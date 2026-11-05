# HAZOP worksheet summary

> **Status:** Internal tabletop simulation, 2026-11-05. The canonical rows are in
> [`../registers/hazards.yaml`](../registers/hazards.yaml); the node/guide-word catalogue is
> in [`nodes.yaml`](nodes.yaml). This is not an independent facilitated HAZOP.

## Nodes

| Node | Area | Hazards |
|---|---|---|
| N01 | Install / SureRoot | HZ-006, HZ-007 |
| N02 | Admin / SureAdmin | HZ-008 |
| N03 | CoverTerms / SureMath | HZ-021 |
| N04 | Payments / r-cash | HZ-022 |
| N05 | Syndicate / LineGrant | HZ-001, HZ-006, HZ-014, HZ-020 |
| N06 | Broker | HZ-013 |
| N07 | Risk | HZ-021 |
| N08 | Slip / subscription | HZ-002, HZ-012, HZ-016 |
| N09 | Line / capabilities | HZ-007, HZ-017 |
| N10 | Distribution / premium | HZ-005, HZ-025 |
| N11 | Policy | HZ-003, HZ-011, HZ-015 |
| N12 | Claim / classification | HZ-004, HZ-018, HZ-019 |
| N13 | Settlement / SureFund | HZ-009 |
| N14 | r-gen / OracleCase | HZ-023 |
| N15 | Books / client | HZ-010, HZ-024 |
| N16 | Install / deploy pipeline | HZ-028, HZ-029 |
| N17 | Capability binding / bundle closure | HZ-030, HZ-031 |
| N18 | External rails | HZ-032, HZ-033 |
| N19 | Test harness truthfulness | HZ-034, HZ-035 |

The install-specific pass is in
[`worksheet-install-2026-11-05.md`](worksheet-install-2026-11-05.md).

## Highest-risk rows

| Hazard | Deviation | Risk | Finding | Disposition |
|---|---|---|---|---|
| HZ-001 | `openLine` takes the syndicate cell twice | high | F-001 | mitigated (fixed) |
| HZ-002 | `bind` takes the slip cell twice | high | F-001 | mitigated (fixed) |
| HZ-003 | policy distribute/open/settle take the cell twice | high | F-001 | mitigated (fixed) |
| HZ-004 | claim settle/dispute take the cell twice | high | F-001 | mitigated (fixed) |
| HZ-005 | distribution run takes the cell twice | high | F-001 | mitigated (fixed) |
| HZ-006 | syndicate/line-grant bundles capture free state | critical | F-002 | mitigated (fixed for install) |
| HZ-007 | line/slip/policy/claim/distribution/broker/risk bundles capture free state | critical | F-002 | mitigated (fixed for install) |
| HZ-008 | global pause is a dead switch | high | F-003 | fixed (R-003) |
| HZ-009 | fund cover/admin nonce split | high | F-004 | mitigated (fixed) |
| HZ-011 | policy expiry leaks line capacity | high | F-006 | mitigated (fixed) |
| HZ-017 | line pays before its state update | high | F-012 | mitigated (fixed) |
| HZ-028 | RSpace continuation cannot decode; no block is produced | critical | F-022 | mitigated (fixed for install) |
| HZ-029 | proposer internal error masked as a Pooled timeout | high | F-025 | mitigated (fixed) |
| HZ-030 | Risk bundle wildcard receive rejects 12_risk | high | F-023 | mitigated (fixed for install) |
| HZ-031 | Slip term omits the authIsOwner top-level binding | high | F-024 | mitigated (fixed for install) |
| HZ-032 | wire codec depth limit is lower than the parser limit | high | F-022 | mitigated (fixed for install) |
| HZ-034 | harness manual propose races an autopropose node | high | F-025 | mitigated (fixed) |

## Method

For each node the tabletop applied the 19 guide words in `nodes.yaml` to the listed
parameters and recorded credible deviations. A hazard row is not a finding by itself; the
finding register carries evidence, impact and the proposed fix. A hazard with no finding is a
control or an accepted operational risk. The tabletop is a desk simulation. The 17-term
install is now E2 green; behavioural reproduction remains incomplete (root suite passes,
the rest are `not_run` or implemented).
