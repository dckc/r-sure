# CoverTerms — concurrency and composition review

> **Status:** Internal review, updated 2026-11-07. Verdict: **safe-by-inspection**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/03_terms.rho`
- State cells: none
- Cross-cell writers: none
- Writers: none
- Readers: fields, values, validate, hash
- Replay guard: `none`
- Bundle publication: top-level, closed

## Review

Stateless or pure component. It has no owned mutable cell; the review checks reply shape, purity, and that it cannot be used to bypass a state owner. The 2026-11-07 refactor replaced the duplicated evidence/claims policy arms with membership tests and a single `termsPolicyOk` helper; dispatch depth is 3.

## Await / value-move notes

- Awaits while holding state: Codec hash
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/03_terms.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: the 2026-11-07 campaign on the refactored tree passed 38/38 run suites, and the local reducer passes; CI run 42386549218 is green.
