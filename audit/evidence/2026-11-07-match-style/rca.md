# RCA-002: state loss on mutating-match refusal paths

## Identity

- **RCA ID:** RCA-002
- **Date:** 2026-11-07
- **Owner:** contracts-audit
- **Severity:** P1
- **Status:** closed
- **HAZOP nodes:** N05, N06, N10, N11, N13
- **Findings:** F-027
- **Hazards:** HZ-037
- **Evidence:** `audit/evidence/2026-11-07-match-style/manifest.json`

## Incident

The match-style audit found 19 mutating matches whose refusal arm replied without
reposting the state cell that had been consumed before the match. The scanner output is
`before-report.txt`. The clearest reachable case is duplicate registration: an owner whose
broker or syndicate is already registered calls registration again, `brokerBookState` or
`syndicateBookState` is consumed before the duplicate check, and the duplicate arm replies
`(false, "duplicate owner", existing)` without reposting. The cell is now empty; every later
read takes or peeks the only datum and blocks.

Component-unavailable and malformed-reply arms have the same shape in `Policy.distribute`,
`Policy.settleClaim`, `Distribution.run`, `Syndicate.withdrawCapital` and `LineSettle.pay`.

## Fault tree

```text
Top event: the instance cell is empty after a refusal (OR)
|- Duplicate registration (AND)
|  |- the registration match consumes brokerBookState/syndicateBookState before dispatch
|  `- the duplicate-owner arm replies without reposting
`- Component failure (AND)
   |- a component lookup or a helper reply returns a non-success tuple
   `- the defensive arm replies without reposting
```

Leaves cite `contracts/src/deploy/10_syndicate.rho`, `11_broker.rho`,
`15_distribution.rho`, `17_policy.rho`, `16_fund.rho`, and the static tool output in
`before-report.txt`.

## Five whys

1. **Why did the instance stop responding?** The state cell was consumed and never
   reposted, so the next take had no datum.
2. **Why was it never reposted?** The refusal arm was written by copying the success arm's
   reply but not its repost.
3. **Why did the copy omit the repost?** The arm sat at depth 4–7 inside a ladder where the
   consume was far above it; the repost was not visible at the refusal site.
4. **Why was the ladder accepted?** There was no rule about mutating-match totality or
   depth; the concurrency review is manual and arm-level.
5. **Why was it not caught earlier?** The behavioural suites exercise success paths; no
   suite drives duplicate registration or a failing component lookup, and no static gate
   linked a mutating match's total arm to a repost.

## Hypotheses

- **H-001** (supported): the duplicate-owner arm in broker and syndicate registration is
  reachable in normal use and loses the book cell.
- **H-002** (supported): component-unavailable and malformed-reply arms lose the object
  cell.
- **H-003** (rejected): the style refactor alone proves the absence of state loss. The gate
  is a shape check; the suites and the local reducer remain the behavioural evidence.

## Root cause

Refusal arms for mutating matches were added without the repost that the success path had,
and the depth ladders separated the consume from the refusal so the ownership was not
visible at the arm. The process gap is the absence of a rule (and a gate) that every
mutating match ends in a total arm that reposts and replies.

## Escape analysis

- The concurrency review is manual; it reasoned about success paths.
- The behavioural suites do not exercise duplicate registration or component failure.
- The static gates checked bundles, captures, money, placeholders and arm inventory, but
  not match totality.
- Deep ladders made the consume and the refusal textually distant.

## Corrective actions

| Action | Owner | Status | Finding | Improvement |
|---|---|---|---|---|
| CA-01 repost on every refusal arm and add total arms | contracts | done | F-027 | R-027 |
| CA-02 add the match-style scanner and wire it into `spec-check` | audit | done | F-026 | R-029 |
| CA-03 flatten the handlers so one consume and one repost are visible per path | contracts | done | F-026 | R-026 |
| CA-04 cover duplicate registration and failure arms in the suites | contracts-audit | open | F-027 | R-027 |

## Verification

| Check | Result | Evidence |
|---|---|---|
| Match gate | pass (0 violations, 0 suppressions) | `gate.txt` |
| Self-test | pass (14 fixture groups) | `self-test.txt` |
| Before inventory | 64 violations (41 M-001, 19 M-004, 4 M-005) | `before-report.txt` |
| After inventory | 0 violations, depth histogram max 3 | `after-report.txt` |
| Parse and normalize | pass on the rendered terms | `make parse-check`, `make normalize-check` |

## Residual risk

- The scanner is heuristic. M-004 accepts a total arm that forwards the cell and reply to a
  helper; the helper is checked independently, but the checker does not prove the call
  completes.
- The behavioural coverage of duplicate registration and component-failure arms is open
  (CA-04); the local reducer exercises the success journey.
- The audit is internal, not independent.
