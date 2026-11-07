# SureFund — concurrency and composition review

> **Status:** Internal review, updated 2026-11-07. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/16_fund.rho`
- State cells: fundState
- Cross-cell writers: none
- Writers: contribute, cover, admin
- Readers: info, balance, covered, shortfalls
- Replay guard: `nonce/govNonce split`
- Bundle publication: top-level, closed

## Review

`contribute` peeks `fundState` for `assetId`, resolves the issuer and amount through helpers, deposits, then consumes the cell once and updates it; the asset read is advisory and is not revalidated after the deposit. `cover` consumes the cell, validates the one-shot cover, creates the facet and reposts before the withdrawal; every refusal reposts. `cover` writes `govNonce` and `fundAdmin` checks it, closing the nonce split (F-004). `cover` is one-shot via `covers[claimId]`. `contribute` is pause-gated; `cover` remains a settlement exemption. The 2026-11-07 refactor extracted the issuer/amount/facet/move helpers and keeps dispatch at depth 3.

## Await / value-move notes

- Awaits while holding state: contribute: peek asset, deposit, then take, cover: fundAdmin then state
- Value moves: contribute, cover
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/16_fund.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: the 2026-11-07 campaign on the refactored tree passed 38/38 run suites, and the local reducer passes; CI run 42386549218 is green.
