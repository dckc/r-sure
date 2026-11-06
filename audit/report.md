# Audit report

> **Status:** Internal desk, tabletop, install-RCA and behavioural review, 2026-11-06.
> **Not an independent audit.** The 17-term install is E2 green after the fixes recorded in
> `rca.yaml#RCA-001`. The campaign records 38 runs, 411 assertions and 0 assertion failures;
> 37 of 40 registered suites pass and three process gates are `not_run`. Install evidence is
> not behavioural coverage. No primitive is audited or production-safe.

## Verdict

The review covered all 30 catalogue components and 46 cross-component interfaces. It found
two systemic P0 source defects, three install-blocking defects, several P1
composition/authorization gaps, and a set of P2 design limits. All P0 findings are fixed in
source. The install now completes: `install-recursion-fix.log` shows all 17 terms deployed
and processed. Three caveats bound that claim:

1. the install RCA's dynamic evidence is the install only; the behavioural campaign and
   the local reducer are separate evidence;
2. the r-cash rail is partial — the account factory installed, but `51_pool` was refused
   with `parse depth exceeded`;
3. three registered process gates remain `not_run`; they are not claimed as passing.

| Metric | Count |
|---|---|
| Catalogue components | 30 |
| Components with a concurrency review | 30 |
| Interfaces in the composition matrix | 46 |
| HAZOP nodes | 19 |
| Public arms registered | 168 |
| Hazards | 36 |
| Findings | 25 |
| P0 findings | 5 (5 fixed; F-002/F-022/F-023/F-024 E2 install) |
| P1 findings | 13 (13 fixed, 0 open) |
| P2/P3 findings | 7 (4 fixed, 3 accepted) |
| Improvements | 25 |
| Tests registered | 40 (37 passing, 3 `not_run`) |
| Lean theorems registered | 285 (register and source agree; no unregistered theorem) |
| Claims | 26 covered, 1 partial, 1 tool; 15 critical primitives covered |

## P0

- **F-001 — take-await-take (fixed).** Eight cornerstone arms took a state cell, awaited an
  external component, then took the same cell again without reposting the first snapshot.
  Fixed by reposting the original snapshot once after the awaits. `tools/check_take_repost.py`
  reports zero for the watched arms.
- **F-002 — unclosed instance bundles (fixed; install E2).** Nine per-object contracts
  published with `bundle+{*X}` while the bundled body captured a state cell or capability.
  All nine now use the rebind pattern and `tools/check_bundle_closedness.py` reports no
  candidates. After the codec and binding fixes, the 17-term install completes.
- **F-022 — RSpace continuation decode (fixed; install E2).** RNodeRust used prost's default
  decode recursion limit of 100. A normalized Par from `10_syndicate` is deeper than 100,
  so the proposer could not decode the RSpace continuation and produced no block;
  `node.log` records 94 `decode continuation failed` errors. Fixed with prost
  `no-recursion-limit` and a 130-deep Par round-trip regression. The node codec test source
  is present; its execution log is not in this evidence set.
- **F-023 — Risk bundle wildcard receive (fixed; install E2).** The bundled `Risk` body used
  `for (@(true, _) <- aCh)`, an open wildcard-binder form. Replaced with the named binder
  `who`; `12_risk` deploys in the 17-term install.
- **F-024 — Slip term missing top-level binding (fixed; install E2).** `13_slip.rho`
  referenced `authIsOwner` without a top-level `new` binding. Added the binding; `13_slip`
  deploys in the 17-term install.

## P1

| Finding | Status | Note |
|---|---|---|
| F-003 dead global pause | fixed | Capacity-creating arms consult `isPaused` and fail closed; claims and value-out arms stay exempt. |
| F-004 fund nonce split | fixed | `fundAdmin` checks `govNonce`; cover writes `govNonce`. |
| F-005 books never populated | fixed | Policy/Claim factories now register in the books. |
| F-006 policy expiry leaks lines | fixed | `Policy.expire` now calls `Line.release`. |
| F-007 `Slip.fundPremium` auth | fixed | Requires the insured. |
| F-008 public `registerDone` | fixed | Removed; `brokerMake` updates the book directly. |
| F-009 fake `SyndicateBook.verify` | fixed | Real URI scan over the book. |
| F-010 no claim period/notice check | fixed | ClaimFactory checks the policy period and notice window. |
| F-011 no slip premium refund | fixed | Slip.expire refunds the funded premium. |
| F-012 line capability/state ordering | fixed | Line takes state first and reposts on every reply. |
| F-020 payable can exceed aggregate | fixed | `SureMath.payable` is the documented minimum and `Policy.settleClaim` propagates refusals without losing state; INV-9 is covered. |
| F-021 settled claim can be re-agreed | fixed | `agree`/`addEvidence`/`classify`/`assess`/`dispute`/`applyDecision` reject terminal status; INV-10 is covered. |
| F-025 harness manual propose masks proposer errors | fixed | The harness now calls manual propose only when configured or `RSURE_FORCE_PROPOSE=1`; the node advertises autopropose. |

## P2/P3

F-013 termsHash is revalidated at bind (fixed); F-014 claim-to-policy binding is accepted as
the policy-token/claims-map boundary; F-015 cross-cell writers and overloaded arms are
declared and checked (fixed); F-016 `distState` catalogue name corrected (fixed); F-017
tri-test presence is accepted with the NAIC off-chain quality note; F-018 external reply
shapes are accepted as an integration boundary; F-019 test register was stale and is synced
to the 36 suites (fixed).

## Install evidence (E2) and its limits

- `audit/evidence/2026-11-05-install-rca/manifest.json` — `rsure.evidence/v2`, scope
  `dynamic: install`, with 25 hashed artifacts.
- `install-recursion-fix.log` — 17/17 terms deployed and processed.
- `devnet-up-recursion-fix.log` and `status-after-fix.json` — fresh single-validator devnet
  and node status.
- `rcash-bootstrap-recursion-fix.log` — account factory installed; `51_pool` refused with
  `parse depth exceeded`. The r-cash pool/market rail is absent.
- `node.log` — baseline 94 `decode continuation failed` proposer errors.
- `audit/registers/rca.yaml#RCA-001` and
  `audit/evidence/2026-11-05-install-rca/rca.md` — fault tree, five whys, hypotheses,
  experiments, escape analysis, corrective actions and residual risk.

The successful install run's own node log is not in the evidence directory; the green claim
rests on the installer's per-term processed output. This is recorded as a residual evidence
gap.

## Audit artifacts

- `audit/concurrency/` — 30 component reviews, pattern vocabulary and verdicts.
- `audit/composition/` — 42 interface rows, reply-shape inventory and assumed invariants.
- `audit/hazop/` — 19-node catalogue, worksheet, install worksheet and the 2026-11-05
  tabletop.
- `audit/registers/` — hazards, findings, improvements, 40 tests, RCA and experiments.
- `audit/rca/template.md` — RCA template.
- `audit/evidence/2026-11-05-concurrency-tabletop/` — pre-fix scanner output and gate notes.
- `audit/traceability/` — generated arm/hazard/finding/test matrix and coverage report.

## Gate status

- Static gates in `make audit-check` pass except `check-audit`, which fails only on the
  Lean theorem-register drift described above.
- New checkers pass: `python3 tools/check_evidence.py`, `python3 tools/check_rca.py`,
  `python3 tools/check_experiments.py`.
- They are not yet in `make audit-check`; the Makefile is owned by the lead. Proposed
  targets: `check-evidence`, `check-rca`, `check-experiments`, appended to `audit-check`.
- `deployments/suite-results.json` records 38 runs, 411 assertions and no assertion
  failure; the coverage report derives 37/40 suites and 126/151 public arms.

## Next steps

1. Run the three `not_run` process gates as first-class campaign rows.
2. Exercise the variance derivation against a live r-gen-approved K-Asset; the devnet test
   uses a stub and the integration suite covers the read shape.
3. Resolve the r-cash `51_pool` parser-depth refusal with the r-cash owner; the r-sure
   install does not depend on it.
4. Run an independent adversarial review and record evidence.
5. Do not describe any primitive as audited until behavioural and independent review
   evidence exists.
