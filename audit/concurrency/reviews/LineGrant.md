# LineGrant — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/10_syndicate.rho`
- State cells: grantState
- Cross-cell writers: none
- Writers: consume, revoke, expire
- Readers: get
- Replay guard: `one-shot status/token`
- Bundle publication: bundle+{*LineGrant} unclosed: captures grantState/slipToken

## Review

`consume` takes `grantState`, validates the slip token and one-shot status, and reposts. `expire` takes the cell, awaits Clock, and reposts. `bundle+{*LineGrant}` captures `grantState` and `slipToken` outside the contract body (P0 bundle, HZ-B1).

## Await / value-move notes

- Awaits while holding state: expire: Clock
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/10_syndicate.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
