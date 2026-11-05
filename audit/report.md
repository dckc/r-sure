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
| Hazards | 27 |
| Findings | 21 |
| P0 findings | 2 (1 fixed, 1 open) |
| P1 findings | 12 (12 fixed, 0 open) |
| P2/P3 findings | 7 (3 fixed/documented, 4 deferred) |
| Improvements | 21 |
| Tests registered | 36 (`not_run`) |
| Lean theorems | 108 component-model theorems |
| Claims | 13 covered, 1 partial, 1 deferred, 1 tool |

## P0

- **F-001 — take-await-take (fixed).** Eight cornerstone arms took a state cell, awaited an
  external component, then took the same cell again without reposting the first snapshot.
  Fixed by reposting the original snapshot once after the awaits. The scanner
  `tools/check_take_repost.py` reports zero for the watched arms after the fix.
- **F-002 — unclosed instance bundles (open for Slip).** Nine per-object contracts published
  with `bundle+{*X}` while the bundled body captured a state cell or capability. Eight now
  use a rebind wrapper and normalize cleanly. `Slip` remains open: its rebind wrapper pushes
  the term past the parser's depth limit, so the fix needs a helper split. **The install
  cannot be called green until this is fixed.**

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
`Bundle's content must not have free variables or wildcards`. Nine instance types were
affected; eight are fixed and the scanner now reports the remaining `Slip` candidate. The
static/parser gates and the Rust core/keystore tests pass; the install and behavioural
campaign are not green.

## Next steps

1. Split `Slip`'s bind/settlement logic into helper contracts, close its bundle, and complete
   `make install`.
2. Run the 36 behavioural suites and record honest pass/fail/not_run.
3. Keep the Lean component model, claims register and flow manifest current; F-003, F-020
   and F-021 are fixed and the behavioural suites remain `not_run` until the devnet install
   clears F-002.
5. Run an independent adversarial review and record evidence.
6. Do not describe any primitive as audited until the above is complete.
