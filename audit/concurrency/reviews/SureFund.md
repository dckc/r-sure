# SureFund — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
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

`contribute` peeks `fundState` for `assetId`, deposits, then takes the cell and updates it (P3; the asset read is not revalidated after the deposit). `cover` takes `fundState`, awaits `fundAdmin`, then reposts before the withdrawal; the cover nonce writes `nonce` while `admin` uses `govNonce`, and `cover` has no `govNonce` replay check (P1). `cover` is one-shot via `covers[claimId]`.

## Await / value-move notes

- Awaits while holding state: contribute: peek asset, deposit, then take, cover: fundAdmin then state
- Value moves: contribute, cover
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/16_fund.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
