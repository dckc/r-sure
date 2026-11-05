# r-share reuse

> **Status:** Interface documented; no r-share change and no devnet suite yet.

r-share can use three r-sure primitives without adopting the insurance market:

- **Distribution**: a one-shot plan over a purse with account, fund and line payees, fixed
  amounts or bps, and a last-bucket remainder. Useful for provider/platform/insurance splits,
  staged refunds and repairer payments.
- **Line**: a risk tranche with credit, pay and release capabilities. Useful when a booking
  needs a cover tranche above a deposit.
- **Policy**: `payable` and `settleClaim` as the read/write boundary for a waiver or excess
  layer.

r-share resolves the relevant factory URI from the r-sure Root and passes its own purse and
tokens. r-sure does not deploy into r-share's Root, and this repository does not modify
r-share. `harness/integration_rshare.py` is an optional consumer test.
