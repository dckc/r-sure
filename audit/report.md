# Audit report

> **Status:** Internal desk and tabletop review, 2026-11-05. **Not an independent audit.**
> No dynamic campaign completed: the devnet install is blocked at the P0 instance-bundle
> defect. Do not describe any primitive as audited or production-safe.

## Verdict

The review covered all 30 catalogue components and 42 cross-component interfaces. It found
two systemic P0 defects, several P1 composition/authorization gaps, and a set of P2 design
limits. The P0 take-await-take defect is fixed in source; the P0 bundle defect is **open**,
so the devnet install and every behavioural suite remain `not_run`.

| Metric | Count |
|---|---|
| Catalogue components | 30 |
| Components with a concurrency review | 30 |
| Interfaces in the composition matrix | 42 |
| HAZOP nodes | 15 |
| Public arms registered | 162 |
| Hazards | 25 |
| Findings | 19 |
| P0 findings | 2 (1 fixed, 1 open) |
| P1 findings | 10 (5 fixed, 5 open) |
| P2/P3 findings | 7 (3 fixed/documented, 4 deferred) |
| Improvements | 19 |
| Tests registered | 36 (`not_run`) |
| Lean theorems | 2 arithmetic theorems |

## P0

- **F-001 — take-await-take (fixed).** Eight cornerstone arms took a state cell, awaited an
  external component, then took the same cell again without reposting the first snapshot.
  Fixed by reposting the original snapshot once after the awaits. The scanner
  `tools/check_take_repost.py` reports zero for the watched arms after the fix.
- **F-002 — unclosed instance bundles (open).** Nine per-object contracts are published with
  `bundle+{*X}` while the bundled body captures a state cell or capability. The node rejects
  the bundle at install. The repair is a closed publication/init pattern. The devnet was
  unavailable during this pass; the unverified unbundling experiment was reverted. **The
  install cannot be called green until this is fixed.**

## P1

| Finding | Status | Note |
|---|---|---|
| F-003 dead global pause | open | `isPaused` is never consulted; wiring touches most mutating arms. |
| F-004 fund nonce split | fixed | `fundAdmin` checks `govNonce`; cover writes `govNonce`. |
| F-005 books never populated | open | Factory-to-book registration is missing. |
| F-006 policy expiry leaks lines | fixed | `Policy.expire` now calls `Line.release`. |
| F-007 `Slip.fundPremium` auth | fixed | Requires the insured. |
| F-008 public `registerDone` | fixed | Removed; `brokerMake` updates the book directly. |
| F-009 fake `SyndicateBook.verify` | fixed | Real URI scan over the book. |
| F-010 no claim period/notice check | open | Needs a Clock check and a regression. |
| F-011 no slip premium refund | open | Needs a value-move path and a regression. |
| F-012 line capability/state ordering | open | Needs a single take/repost around the capability. |

## P2/P3

F-013 termsHash not revalidated at bind; F-014 claimId not bound to the policy/line;
F-015 cross-cell writers and overloaded arms are under-declared; F-016 `distState` catalogue
name corrected; F-017 tri-test checks presence, not quality (documented in the NAIC primer);
F-018 external reply shapes are assumed; F-019 test register was stale and is now synced to
36 suites.

## Evidence

- `audit/concurrency/` — 30 component reviews, pattern vocabulary and verdicts.
- `audit/composition/` — 42 interface rows, reply-shape inventory and assumed invariants.
- `audit/hazop/` — 15-node catalogue, worksheet and the 2026-11-05 tabletop.
- `audit/registers/` — hazards, findings, improvements, 36 tests and Lean theorems.
- `audit/evidence/2026-11-05-concurrency-tabletop/` — pre-fix scanner output and gate notes.

## Known install blocker

A devnet install reaches `16_fund.rho`; `10_syndicate.rho` is refused with
`Bundle's content must not have free variables or wildcards`. The scanner finds nine affected
instance types, not only `Syndicate`/`LineGrant`. The static/parser gates and the Rust
core/keystore tests pass; the install and behavioural campaign are not green.

## Next steps

1. Fix F-002 with a closed publication/init pattern and complete `make install`.
2. Run the 36 behavioural suites and record honest pass/fail/not_run.
3. Fix the remaining open P1s (F-003, F-005, F-010, F-011, F-012) with regressions.
4. Complete the Lean model and flow manifest.
5. Run an independent adversarial review and record evidence.
6. Do not describe any primitive as audited until the above is complete.
