# Syndicate — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/10_syndicate.rho`
- State cells: syndicateState
- Cross-cell writers: none
- Writers: setManager, contribute, withdrawCapital, quote, revokeQuote, expireQuote, openLine, suspend, resume
- Readers: info, capacity, quotes, quote, lines, line, members, member
- Replay guard: `nonce/quotes`
- Bundle publication: bundle+{*Syndicate} unclosed: captures syndicateState

## Review

`quote` is the correct pattern: take, repost before `rs!`, then a second take and repost. `openLine` takes `syndicateState`, awaits LineGrant/LineFactory, then takes the same cell again without a repost (P0 take-await-take, HZ-C1). `contribute` deposits before the state update; a failed update can hang (P3 concern). `withdrawCapital` updates state before the value move and uses `1/0` on failure. `expireQuote` takes the cell then awaits Clock.

## Await / value-move notes

- Awaits while holding state: openLine: LineGrant, LineFactory, quote: rs grant publication after repost, withdrawCapital: Payments, expireQuote: Clock
- Value moves: contribute, withdrawCapital, lineSettleCap.pay
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/10_syndicate.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
