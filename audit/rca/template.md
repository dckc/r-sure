# RCA template

> Copy this file into `audit/evidence/<date>-<slug>/rca.md` and add a matching record to
> `audit/registers/rca.yaml`. The YAML record is normative; this narrative is the readable
> account. Do not call an RCA closed without an E2 verification or an explicit, reasoned
> residual-risk entry.

## Identity

- **RCA ID:** RCA-NNN
- **Date:** YYYY-MM-DD
- **Owner:** role
- **Severity:** P0 | P1 | P2 | P3
- **Status:** open | closed | monitoring
- **HAZOP nodes:** NNN, NNN
- **Findings:** F-NNN, F-NNN
- **Hazards:** HZ-NNN, HZ-NNN
- **Evidence:** `audit/evidence/<date>-<slug>/manifest.json`

## Incident

What failed, when, and what the operator saw. Separate the observed symptom from the
claim about the cause. Quote the exact error text and the artifact that contains it.

## Fault tree

State the top event and the gate structure. Every leaf needs an evidence reference;
every internal node is `AND` or `OR`. A branch with no evidence is a hypothesis, not a
cause.

```text
Top event (OR)
|- Branch A (AND)
|  |- leaf: cause with evidence
|  `- leaf: cause with evidence
`- Branch B (AND)
   |- leaf: cause with evidence
   `- leaf: cause with evidence
```

## Five whys

1. Why ...?
2. Why ...?
3. Why ...?
4. Why ...?
5. Why ...?

The fifth answer should name the control or design gap that let the defect escape.

## Hypotheses

| ID | Statement | Status | Evidence |
|---|---|---|---|
| H-NNN | ... | supported / rejected / partial / inconclusive | X-NNN |

A rejected hypothesis is a result; keep it in the record. Do not delete the hypotheses
that the evidence ruled out.

## Experiments

| ID | Question | Method | Artifact | Result | Conclusion |
|---|---|---|---|---|---|
| X-NNN | ... | ... | ... | pass / fail / inconclusive / blocked | supports / rejects H-NNN |

Every experiment names an artifact that exists. A result that was not executed is
`inconclusive` or `blocked` with a reason, never a pass.

## Root cause

One paragraph. Name the defect, the layer, and why the layer's contract was inconsistent
with the layer above or below it. List contributing defects separately; do not promote a
contributing defect to the root cause because it was easier to fix.

## Escape analysis

Why did the existing static gates, tests, review and evidence not catch this? Name each
gate that should have caught it and the property it did not model. Include the harness and
reporting path if it hid the real error.

## Corrective actions

| ID | Action | Owner | Status | Finding | Improvement |
|---|---|---|---|---|---|
| CA-NNN | ... | ... | done / open | F-NNN | R-NNN |

## Verification

Record the E2 check that shows the fix works, and the checks that did not run. A green
install is install evidence only; it is not behavioural suite coverage.

- Install: pass / fail / not_run — artifact
- Devnet: pass / fail / not_run — artifact
- Node codec or unit regression: pass / fail / implemented-not-executed — artifact
- Behavioural suites: pass / fail / not_run — artifact and reason

## Residual risk

List what remains unproven, external, or only partially mitigated. State the audit scope:
internal, not independent, no production-safety claim.
