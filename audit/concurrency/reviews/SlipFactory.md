# SlipFactory — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/13_slip.rho`
- State cells: none
- Cross-cell writers: none
- Writers: none
- Readers: open
- Replay guard: `none`
- Bundle publication: publishes Slip with unclosed bundle

## Review

Stateless factory. It performs broker, risk, terms and payments lookups, creates a purse, then calls `slipMake`. `Slip` is published with `bundle+{*Slip}`, which captures `slipState`, the purse and tokens (P0 bundle). The factory does not validate the risk/insured fields itself; that is delegated to the caller and `Slip`.

## Await / value-move notes

- Awaits while holding state: open: broker/risk/terms/payments then slipMake
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/13_slip.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
