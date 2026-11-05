# Invariants

> **Status:** Implemented (source + static/parser gates); a Lean component model now proves
> the economic core. `proved-model` is not a Rholang refinement. See
> `formal-model.md` and `proof-map.md`.

The simulator and the audit use the same numbering as `spec/invariants.md`.

| ID | Invariant | Business meaning | Lean status |
|---|---|---|---|
| INV-1 | Capacity | A syndicate never promises more than its capital: `committed + written <= capital` and free capacity is non-negative. | covered |
| INV-2 | Subscription | A slip that binds is fully placed: shares sum to 10000 bps and every line is bound. | covered |
| INV-3 | Exposure | Line exposures add up to the policy aggregate; the last line absorbs the integer remainder. | covered (model) |
| INV-4 | Premium | Commission, central-fund levy and line credits add up to the premium, with no value created or lost. | covered |
| INV-5 | Payable | The payable is the agreed amount after the per-claim, aggregate and deductible caps the contract applies. | covered |
| INV-6 | Settlement | Line payouts plus the central-fund cover equal the payable. | covered |
| INV-7 | Line | A line never pays more than its exposure, and exposure never exceeds the written capital behind it. | covered (model) |
| INV-8 | Exactly once | A claim is paid at most once per line, once per policy, and the fund covers it at most once. | covered |
| INV-9 | Aggregate | Each settlement reduces the aggregate remaining and never drives it negative. | covered |
| INV-10 | Terminal | Settled/denied claims and expired policies cannot be re-opened or re-paid. | partial: missing guards recorded |
| INV-11 | Atomicity | A failed deploy leaves no partial value move. | partial: native ERTP assumed |
| INV-12 | Pause | Global pause does not block settlement, close, expiry or refunds. | deferred: F-003 open |

## Modelling notes

- The model is list-based and uses `Nat` identifiers and amounts. Rholang maps, URIs,
  capabilities and purses are abstracted or kept as boundary assumptions.
- `payable` follows the contract's branch order. The prose `min(agreed, perClaimLimit,
  aggregateRemaining)` is only equivalent when `agreed < perClaimLimit` or
  `aggregateRemaining >= perClaimLimit`; the contract itself caps at the per-claim limit when
  the agreed amount reaches it.
- INV-10 is a target. `Claim@"agree"` and `Claim@"addEvidence"` reject some terminal states
  but not all; the model proves the intended guard and the gap is recorded in
  `claims.yaml`.
- INV-11 and INV-12 are boundaries, not theorems over ERTP or the node.
