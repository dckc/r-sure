# r-share damage waiver

> **Status:** Mapping only. r-share is not modified by this repository.

An r-share booking has a deposit and a remedy table. A damage waiver layers an r-sure policy
above the deposit:

- The guest pays the rental plus a waiver premium.
- The deposit covers the first tranche of damage (r-share's existing Bond).
- The r-sure policy covers the excess above the deposit, up to its per-claim limit.
- A damage claim is notified by the provider or the r-share claim flow; the r-sure claim
  settles to the provider's r-cash account.
- If the booking is cancelled, the waiver premium refund follows the booking's cancellation
  remedy.

The reusable interfaces are:

- `DistributionFactory` / `Distribution` — a one-shot account/fund/line waterfall. It can pay
  a repairer, refund a deposit and retain a provider fee with exact conservation.
- `Line` — a risk tranche with credit, pay and release capabilities.
- `Policy` — `payable` and `settleClaim` are the read and write boundaries.

r-share may call these patterns as a library; it does not depend on r-sure's Root and this
repository does not deploy into r-share's.
