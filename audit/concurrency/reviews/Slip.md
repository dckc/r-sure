# Slip — concurrency and composition review

> **Status:** Internal review, 2026-11-05. Verdict: **finding**. This is a desk review, not
> an independent audit or a dynamic test.

## Ownership

- Deploy file: `contracts/src/deploy/13_slip.rho`
- State cells: slipState
- Cross-cell writers: none
- Writers: accept, subscribe, fundPremium, bind, expire
- Readers: info, subscriptions, subscription, premium, policy
- Replay guard: `nonce/tokens`
- Bundle publication: bundle+{*Slip} unclosed: captures slipState/purse/tokens

## Review

`bind` takes `slipState`, opens lines, creates the policy and distributes the premium, then takes `slipState` again without a repost (P0 take-await-take, HZ-C3). `subscribe` holds the cell across `Syndicate.quote` (P2). `fundPremium` authenticates an owner but does not check that it is the insured (P1). `expire` does not refund a funded premium (P1). `bundle+{*Slip}` is unclosed.

Slip-level pause gates were omitted because `13_slip.rho` exceeds the node parser depth with any added wrapper. Binding is blocked through the gated `Syndicate.quote`/`openLine` capacity path; this is recorded in F-003 and R-003.

## Await / value-move notes

- Awaits while holding state: subscribe: Syndicate.quote while state held, bind: lines/policy/distribution
- Value moves: fundPremium
- Refusals before effects? Reviewed arm by arm in the source; see `components.yaml` for the
  per-arm inventory and `../composition/interfaces.yaml` for callee reply shapes.

## Evidence

- Source: `contracts/src/deploy/13_slip.rho`
- Static scanners: `tools/check_take_repost.py`, `tools/check_bundle_closedness.py`,
  `tools/check_reply_shapes.py`, `tools/check_pause_scope.py`
- Dynamic evidence: not run (devnet install blocked at the P0 bundle defect).
