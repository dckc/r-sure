# HAZOP worksheet — install and deploy pipeline 2026-11-05

> **Status:** Internal desk worksheet for the install RCA. Not an independent facilitated
> HAZOP. The normative hazard rows are in `../registers/hazards.yaml` (HZ-028 … HZ-035);
> this worksheet records the guide-word pass that produced them.

## Scope

Nodes N16–N19 in [`nodes.yaml`](nodes.yaml):

| Node | Area | Parameters applied |
|---|---|---|
| N16 | Install / deploy pipeline | term, continuation, deploy result, block height |
| N17 | Capability binding / bundle closure | bundle binding, term binding |
| N18 | External rails | node image, parser depth, continuation, deploy result |
| N19 | Test harness truthfulness | propose mode, evidence scope, deploy result |

Inputs: `contracts/src/deploy/*.rho`, `harness/install.py`, `harness/deploy.py`, the
RNodeRust tree at `/home/patrick/RNodeRust`, and the evidence in
`audit/evidence/2026-11-05-install-rca/`. The guide words are the 19 in `nodes.yaml`.

## Worksheet

| # | Node | Guide word | Parameter | Deviation | Cause | Consequence | Hazard | Finding | Control | Disposition |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | N16 | LOST | continuation | The proposer cannot decode the RSpace continuation; no block is produced | prost decode recursion limit 100 below normalized Par depth | Chain stops; deploy stays Pooled | HZ-028 | F-022 | prost `no-recursion-limit`; 130-deep round-trip; pinned node image | mitigate |
| 2 | N16 | UNAVAILABLE | deploy result | A failed proposal is reported as a 180 s Pooled timeout, not the node error | wait loop has no internal-error branch; harness calls manual propose | Failure misattributed to the contract | HZ-029 | F-025 | autopropose-aware propose; strict propose for diagnosis | mitigate |
| 3 | N16 | AFTER | block height | The installer treats a term as deployed before the proposer has advanced the chain | deploy result conflates Pooled with pending | Install order can advance on a stalled chain | — | — | per-term processed result; block advance check | monitored |
| 4 | N17 | PART OF | bundle binding | Bundled Risk body uses `for (@(true, _) <- aCh)`; wildcard binder leaves the bundle open | wildcard auth receive; scanner did not model the class | 12_risk rejected; install stops | HZ-030 | F-023 | named binder `who`; bundle scanner | mitigate |
| 5 | N17 | LOST | term binding | `authIsOwner` is referenced without a top-level `new` binding | top-level binding list incomplete | 13_slip rejected; Slip arms not published | HZ-031 | F-024 | bind `authIsOwner`; install E2 | mitigate |
| 6 | N17 | AS WELL AS | bundle binding | A helper name is bound in one term but reused in a bundled body that does not close over it | no binding-set check | Deploy fails at parse/binding time | — | — | future name/binding gate (`CA-06` scope) | open |
| 7 | N18 | OTHER THAN | parser depth | Wire codec imposes a lower depth limit than the parser and normalizer | prost decode default only | Valid term encodes but cannot decode | HZ-032 | F-022 | single codec limit; deep test | mitigate |
| 8 | N18 | OTHER THAN | parser depth | r-cash `51_pool` exceeds the node parser depth; bootstrap refuses the pool | upstream r-cash term depth | Account factory present, pool/market absent | HZ-033 | — | account factory verified; residual risk recorded | open (external) |
| 9 | N18 | STALE | node image | A rebuilt node is not the image that produced an earlier log | image digest not recorded in every run | Evidence and behaviour can be mismatched | — | — | `node-image.txt` digest; manifest pins the image | monitored |
| 10 | N19 | UNAVAILABLE | propose mode | Harness calls manual propose when the node advertises autopropose | `_propose_once` unconditional | Races proposer; masks error | HZ-034 | F-025 | `_manual_propose` default false | mitigate |
| 11 | N19 | STALE | evidence scope | Install-green evidence is read as behavioural coverage while the behavioural campaign is incomplete | evidence v1 lacks a scope field | Overstated audit coverage | HZ-035 | — | evidence v2; report/README wording; checkers | mitigate |
| 12 | N19 | EARLY | evidence scope | A fixed finding is marked verified before its regression suite runs | static change plus install conflated with behavioural verification | Fixed != behaviourally tested | — | — | tests register keeps the behavioural campaign honest (root passes, rest not_run); report says install-only | monitored |

Rows 3, 6, 9 and 12 are controls or observations, not findings. They are kept so the
worksheet does not imply that only recorded findings were considered.

## Guide words with no credible deviation

| Guide word | Reason |
|---|---|
| NO/NOT | A missing term is caught by the fixed install order; the installer stops on a missing file. |
| MORE / LESS | Term size and block height are bounded by existing deploy and parser limits; already covered by the build and measure gates. |
| REVERSE | Deploy order is sequential and has no reverse path; a rollback is a fresh install. |
| BEFORE | Preflight runs before install and refuses a non-ready node. |
| REPEAT | Retrying a value-moving deploy is governed by the opId rule in `AGENTS.md`; install terms are not value-moving. |
| CONCURRENT | The devnet is a single validator; install terms are sequential and deploys do not interleave. |
| DUPLICATE | A duplicate deploy is rejected by the opId/nonce domain; install uses fresh signatures per term. |
| UNKNOWN | An unknown deploy result is treated as pending until timeout, which is recorded as HZ-029. |
| UNAUTHORIZED | Install authority is the deployer key; out of scope for this worksheet. |
| LATE | A late proposal is a liveness symptom, recorded as HZ-028. |

## Decisions

- **D-13 (N16, LOST).** Treat `decode continuation failed` as a node codec defect, not a
  contract refusal. Fix in RNodeRust (R-022). Record F-022/HZ-028/HZ-032.
- **D-14 (N17, PART OF).** Replace the wildcard auth binder with a named binder (R-023).
  Record F-023/HZ-030.
- **D-15 (N17, LOST).** Add `authIsOwner` to the Slip top-level `new` (R-024). Record
  F-024/HZ-031.
- **D-16 (N19, UNAVAILABLE).** Make the harness autopropose-aware (R-025). Record
  F-025/HZ-029/HZ-034.
- **D-17 (N18, OTHER THAN).** The r-cash `51_pool` refusal is an external rail residual,
  not an r-sure contract finding. Keep the r-sure install green claim separate from a
  complete r-cash rail claim. Record HZ-033.
- **D-18 (N19, STALE).** Evidence moves to schema v2 with an explicit scope; install E2
  is not behavioural coverage. Record HZ-035 and the RCA.

## Limitations

- Internal desk pass; no independent facilitator.
- The RCA dynamic evidence is the 17-term install only. The behavioural campaign is
  incomplete: the root suite passes, the other registered suites are `not_run` or
  implemented, and none of that run is covered by the install E2.
- The r-cash rail is partial: the account factory installed, the pool was refused.
- The successful install run's own node log is not in the evidence directory; the green
  claim rests on the installer's per-term processed output.
