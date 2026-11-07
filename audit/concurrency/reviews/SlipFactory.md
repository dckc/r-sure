# SlipFactory — concurrency and composition review

> **Status:** Internal review, updated 2026-11-07. Verdict: **concern**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/13_slip.rho`
- State cells: none
- Cross-cell writers: none
- Writers: none
- Readers: open
- Replay guard: `none`
- Bundle publication: publishes Slip after the rebind fix; check_bundle_closedness reports no candidates

## Review

Stateless factory. It resolves the broker, terms and payments components, validates and hashes the terms, creates the purse, and calls `slipMake`; the stages are `slipOpenBroker`, `slipOpenTerms`, `slipOpenPayments`, `slipOpenPurse` and `slipOpenHeight`, each at depth 2 or less. A failing lookup or helper reply returns the refusal to the caller instead of leaving a receive waiting. `Slip` is published after the rebind fix; `check_bundle_closedness` reports no candidates. The factory does not validate the risk/insured fields itself; that is delegated to the caller and `Slip`.

## Await / value-move notes

- Awaits while holding state: open: broker/risk/terms/payments then slipMake
- Value moves: none
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/13_slip.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: the last full campaign (2026-11-06) passed the relevant suites; the 2026-11-07 refactor is covered by `make spec-check`, the local reducer and CI run 42386549218. The full campaign must be rerun.
