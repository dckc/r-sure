# RCA — install blocked by RSpace continuation decode

- **RCA ID:** RCA-001
- **Date:** 2026-11-05
- **Owner:** audit
- **Severity:** P0
- **Status:** closed for install; behavioural verification remains open
- **HAZOP nodes:** N16 install/deploy pipeline, N17 capability binding/bundle closure,
  N18 external rails, N19 test harness truthfulness
- **Findings:** F-022 (continuation decode), F-023 (Risk wildcard bundle), F-024 (Slip
  missing binding), F-025 (masked proposer)
- **Hazards:** HZ-028 … HZ-035
- **Normative record:** `audit/registers/rca.yaml#RCA-001`
- **Evidence:** `audit/evidence/2026-11-05-install-rca/manifest.json`

> **Scope.** Internal RCA, not an independent review. The E2 evidence is the 17-term
> install only. The behavioural campaign is incomplete: the root suite passes, the other
> registered suites are `not_run` or implemented, and none of that run is covered by this
> record.

## Incident

`make install` stopped at the `12_risk` term. The deploy API returned
`{"NotProcessed":{"status":"Pooled"}}` until the harness's 180-second timeout
(`install-baseline.log`). The node log shows the proposer failing 94 consecutive times:

```text
ERROR [coop.rchain.node.instances.ProposerInstance] propose failed with an internal
error: decode continuation failed — no block was produced, so the chain will not
advance until this is fixed
```

The symptom was a deploy timeout. The cause was a node-side failure to decode the
RSpace continuation on the next proposal, so the chain never advanced.

## Fault tree

```text
Install cannot complete and the chain cannot advance (OR)
|- RSpace continuation decode fails on the next proposal (AND)
|  |- prost default decode recursion limit is 100
|  |- the normalized Par from 10_syndicate is deeper than 100
|  `- no regression decoded a deep Par on the RSpace path
|- the 12_risk deploy is rejected (AND)
|  |- the bundled Risk body uses a wildcard auth receive
|  `- the static bundle scanner did not model the wildcard-binder class
|- the 13_slip deploy is rejected (AND)
|  |- authIsOwner is absent from the Slip term's top-level new
|  `- no gate compares helper names with top-level bindings
`- the harness masks the node internal error (AND)
   |- the deploy stays Pooled until the 180-second timeout
   `- the harness calls manual propose while the node advertises autopropose
```

All leaves carry evidence in `audit/registers/rca.yaml`. The first branch is the root
cause; the last branch is why the root cause was initially misread as a contract defect.

## Five whys

1. **Why did the install stop?** The `12_risk` deploy never reached a processed state;
   it stayed Pooled until the client timeout.
2. **Why did it stay Pooled?** The proposer produced no block, so no deploy could be
   included or processed.
3. **Why did the proposer produce no block?** It failed to decode the RSpace
   continuation and logged `decode continuation failed` on every attempt.
4. **Why did the decode fail?** RNodeRust's Par wire codec used prost's default decode
   recursion limit of 100, while the normalized Par from `10_syndicate` was deeper than
   100.
5. **Why was the mismatch not caught earlier?** Codec tests covered encode and shallow
   round-trips, not a deep decode; the harness timeout hid the proposer error; install
   was the only E2 path; and no static gate exercised the node codec. The same pass also
   found two contract binding defects and an autopropose race that made the failure
   harder to read.

## Hypotheses

| ID | Statement | Status | Evidence |
|---|---|---|---|
| H-001 | A contract-logic defect in `12_risk` alone causes the stall | partial | 12_risk had a wildcard-binder defect, but the chain stall was the codec (X-001, X-002) |
| H-002 | prost's default decode limit (100) is below the normalized Par depth | supported | X-002, X-003, X-004, X-005 |
| H-003 | Calling manual propose on an autopropose node is the root cause | rejected | X-006 removes it and the install still fails |
| H-004 | The Risk wildcard auth receive rejects the 12_risk deploy | supported | X-007, X-005 |
| H-005 | Missing `authIsOwner` rejects the 13_slip deploy | supported | X-008, X-005 |
| H-006 | The same fix fully bootstraps the r-cash rail | rejected | X-009: `51_pool` refused with parse depth exceeded |
| H-007 | A green install verifies contract behaviour | rejected | X-010: only the root suite passes; the install does not exercise behaviour |

## Experiments

| ID | Question | Artifact | Result | Conclusion |
|---|---|---|---|---|
| X-001 | Does the failure reproduce? | `install-baseline.log`, `node.log` | fail (reproduced) | inconclusive on cause |
| X-002 | Is the proposer, not the contract, failing? | `node.log` | pass | supports H-002 |
| X-003 | Does the codec use prost's default recursion limit? | `models/Cargo.toml`, `models/src/wire.rs` | pass | supports H-002 |
| X-004 | Is there a deep-Par decode regression? | `deep_par_codec.rs` | pass (static) | supports H-002 |
| X-005 | Does the rebuilt node install all terms? | `install-recursion-fix.log` | pass | supports H-002/H-004/H-005 jointly |
| X-006 | Does removing manual propose alone unblock? | `install-no-manual-propose.log` | fail | rejects H-003 |
| X-007 | Is the Risk wildcard binder gone? | `contracts/src/deploy/12_risk.rho` | pass | supports H-004 |
| X-008 | Is `authIsOwner` bound at the top level? | `contracts/src/deploy/13_slip.rho` | pass | supports H-005 |
| X-009 | Is the r-cash rail complete? | `rcash-bootstrap-recursion-fix.log` | fail | rejects H-006 |
| X-010 | Does install verify behaviour? | `deployments/suite-results.json` | fail (root only) | rejects H-007 |

X-004 is static: the test source is present, but its execution log is not in this
evidence set. X-005 verifies the fixes jointly; it does not isolate each contract fix.

## Root cause

**Root cause (F-022).** RNodeRust built its Par wire codec with prost's default decode
recursion limit of 100. The parser and normalizer accept and normalize deploy terms
deeper than that, so a valid term encodes but the RSpace continuation cannot be decoded
on the next proposal. The proposer builds no block, and the chain stops. The encode path
had no matching limit; only decode imposed the second, lower depth contract.

Contributing defects in the same install:

- **F-023:** the bundled `Risk` body received the auth reply with a wildcard binder,
  `for (@(true, _) <- aCh)`, which is open under the wildcard-binder bundle class.
- **F-024:** `13_slip.rho` did not bind `authIsOwner` in the top-level `new` sequence.
- **F-025:** `harness/deploy.py` always called manual propose. The node advertised
  `autopropose:true` and `manualPropose:false`, so the extra call raced the node proposer
  and the deploy timeout hid the node's internal error. This is a masking and race
  factor, not the root cause: removing it alone did not make the install pass (X-006).

## Escape analysis

- The static gates (build, measure, architecture, captures, select, placeholders, money,
  suites) never execute the node codec or the RSpace continuation path.
- `parse-check` parses terms with the target parser but does not encode, normalize and
  decode a continuation at the depth the parser accepts.
- Codec tests covered encode and shallow round-trips; no test decoded a Par deeper than
  prost's default limit.
- The harness converted a proposer internal error into a generic Pooled timeout, so the
  contract under deploy looked responsible.
- Evidence schema v1 had no scope field, so install evidence and behavioural coverage
  could be conflated in prose.
- The bundle scanner modelled free names but not the wildcard-binder bundle class, and
  no gate compared helper names with a term's top-level binding set.

## Corrective actions

| ID | Action | Owner | Status | Finding | Improvement |
|---|---|---|---|---|---|
| CA-01 | Enable prost `no-recursion-limit`; add 130-deep Par round-trip | platform-node | done | F-022 | R-022 |
| CA-02 | Named auth binder in Risk arms | contracts | done | F-023 | R-023 |
| CA-03 | Bind `authIsOwner` in the Slip top-level new | contracts | done | F-024 | R-024 |
| CA-04 | Autopropose-aware harness | harness | done | F-025 | R-025 |
| CA-05 | Evidence v2 and evidence/RCA/experiment checkers | audit | done | F-025 | R-025 |
| CA-06 | Complete the behavioural campaign honestly (root passes) | audit-contracts | open | — | — |
| CA-07 | Resolve r-cash `51_pool` parser depth with the r-cash owner | external-rcash | open | — | — |
| CA-08 | Wire the three new checkers into `make audit-check` | lead | open (Makefile owned by lead) | — | — |

## Verification

| Check | Result | Artifact |
|---|---|---|
| Install, 17 terms | **pass** | `install-recursion-fix.log` |
| Fresh devnet and preflight | **pass** | `devnet-up-recursion-fix.log`, `status-after-fix.json` |
| Node codec regression | implemented, not executed in this evidence set | `../RNodeRust/rholang/tests/deep_par_codec.rs` |
| r-cash bootstrap | **partial**: account factory installed; `51_pool` refused with parse depth exceeded | `rcash-bootstrap-recursion-fix.log` |
| Behavioural suites | **partial**: root passes; the other registered suites are not_run or unimplemented | `deployments/suite-results.json` |

Evidence gap: the successful install log is present, but the node log for that specific
run is not in this directory. The last node logs in the directory predate the rebuild and
still show the decode error. The green claim rests on the installer's per-term processed
output in `install-recursion-fix.log`.

## Residual risk

- The behavioural campaign is incomplete: the root suite passes, but the install proves
  deployment and block progress, not capacity, subscription, premium, claim or settlement
  behaviour.
- The deep-Par regression is 130 levels. A future term deeper than that may hit a new
  limit or cost bound; the node image is pinned by digest only for this evidence.
- The r-cash pool and market rail are absent on this devnet after the `51_pool` parse
  depth refusal. Any r-sure suite that needs the pool is blocked until r-cash fixes it.
- `RSURE_FORCE_PROPOSE=1` remains an escape hatch and can reintroduce the race if used
  on an autopropose node.
- The audit remains internal and is not an independent review. No production-safety
  claim is made.
