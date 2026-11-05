# Concurrency review

> **Status:** Internal desk review, 2026-11-05. Not an independent audit. Dynamic evidence
> is `not_run` until the devnet install clears the P0 bundle defect.

Every component in `contracts/components.json` has exactly one row in `components.yaml` and
one file in `reviews/`. The gate `tools/check_concurrency_audit.py` fails if a component is
missing, if a verdict is `not-reviewed`, or if a hazard/finding reference does not resolve.

## Pattern vocabulary

Adapted from the Rholphin primitive review:

- **P1** — take → validate → post, with no external await while the cell is held.
- **P2** — peek → await → take → revalidate → post. A peek is only a hint; the take must
  revalidate.
- **P3** — peek → effect → take → revalidate → post. The effect must not depend on stale
  peeked state.
- **P4** — hold a cell only across a native ERTP operation where no re-entrant path exists.
- **REV** — monotonically increasing revision/nonce.
- **OPI** — idempotency key (`opId`/nonce) checked before a second effect.
- **ERTP** — native purse/facet reply shapes and value-move ordering.
- **PHASE** — pre-effect refusal vs post-effect `1/0` rollback.

## Verdicts

| Verdict | Meaning |
|---|---|
| `safe-by-inspection` | No finding; the arm matches P1/P2/P3 and the reply shapes are understood. |
| `concern` | A design concern or an untested assumption; no confirmed P0/P1. |
| `finding` | A confirmed issue is recorded in `../registers/findings.yaml`. |
| `not-applicable` | Pure arithmetic with no state or composition; only for a justified component. |

## What each review records

- owned state cells and cross-cell writers;
- mutating arms and their take/repost discipline;
- a second take without an intervening repost;
- peeks used before an await;
- external awaits and hang points;
- `1/0` sites and whether they are before or after a value move;
- parallel joins and capability flow;
- bundle publication and closedness;
- replay guard (`opId`/`nonce`/`govNonce`/token);
- composition calls and the callee reply shapes;
- verdict, source references and evidence.

## Known systemic results

- Eight cornerstone arms had a take → await → take defect before remediation (see
  `../registers/findings.yaml`, F-001).
- Nine per-object instance types were published with a bundle that captures a state cell or
  capability outside the contract body (F-002). The node rejects these at install.
- The global pause was dead (F-003), and `SureFund` mixed `nonce`/`govNonce` (F-004).
- The books were never populated (F-005); `Policy.expire` did not release lines (F-006).

The reviews are updated after remediation; the pre-remediation candidates are preserved in
`../evidence/2026-11-05-concurrency-tabletop/`.
