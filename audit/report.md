# Audit report

> **Status:** In progress. No completed independent audit.

## Current state

- 163 public arms registered; 3 hazards recorded.
- 0 confirmed findings; 0 improvements; 0 Lean theorems registered.
- Static and parser gates pass.
- Behavioural suites are scaffolded; most report `not_run`.

## Known install blocker

A devnet install reaches `16_fund.rho`; `10_syndicate.rho` is refused with
`Bundle's content must not have free variables or wildcards`. The `Syndicate` and `LineGrant`
instance contracts capture creation parameters, and `bundle+{*…}` publication needs a
refactor to a closed bundle (for example a per-instance maker contract with the captured
names passed as arguments). The static/parser gates and the Rust core/keystore tests pass;
the install and behavioural campaign are not green.

## Next steps

1. Refactor instance-contract publication and complete the devnet install.
2. Run the behavioural campaign (root, payments, syndicate, capital, broker, risk, slip,
   binding, line, policy, distribution, premium, fund, claim lifecycle, settlement,
   conservation, r-cash, r-gen).
3. Complete the Lean model and flow manifest.
4. Run an independent adversarial review and record findings with evidence.
5. Do not describe any primitive as audited until the above is complete.
