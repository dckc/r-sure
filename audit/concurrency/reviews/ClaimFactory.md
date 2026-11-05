# ClaimFactory — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/18_claim.rho`
- State cells: none
- Cross-cell writers: none
- Writers: none
- Readers: create
- Replay guard: `none`
- Bundle publication: publishes Claim with unclosed bundle

## Review

Stateless factory. It creates `Claim` and publishes it with `bundle+{*Claim}`; the bundled body captures `claimState` and the claim token (P0 bundle).

## Await / value-move notes

- Awaits while holding state: rs bundle publication
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/18_claim.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
