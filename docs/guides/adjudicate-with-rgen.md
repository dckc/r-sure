# Adjudicate with r-gen

> **Status:** Mapping only; the r-gen OracleCase protocol is matched in the contract.

r-gen's `OracleFactory.open(dId, subjectRef, caseReq, subjectApply, ret)` takes the subject's
private apply capability. r-sure's claim supplies its `applyDecision` capability.

`caseReq` carries:

- `kind`: `rsure.claim.dispute`
- `openedBy`: the deployer's address
- `parties`: insured, broker and adjuster
- `groundsHash`: the dispute grounds
- `requirement`: the credential scope, e.g. `InsuranceAdjuster`, level 2
- `adjudicator` and `adjudicatorCredentialUri`
- `deadlineHeight`

The adjudicator calls `OracleCase.decide` with `uphold`, `partial` or `revoke`, then
`OracleCase.execute`. The execution calls `Claim.applyDecision(caseId, decision, ret)`, which
maps:

| Outcome | Claim result |
|---|---|
| `uphold` | assessment amount agreed; status `upheld` |
| `partial` | decision amount agreed; status `partially_upheld` |
| `revoke` | zero agreed; status `denied` |

The apply capability checks the case id and is one-shot. A second execution is refused by
r-gen's case state, not by r-sure.
