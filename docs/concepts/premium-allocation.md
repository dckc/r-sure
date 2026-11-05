# Premium allocation

> **Status:** Implemented (source + static/parser gates).

The insured funds the full premium before binding. The slip holds the premium in a
contract-owned purse; at bind the policy takes the purse and runs one `Distribution`:

```
commission = premiumTotal * brokerCommissionBps / 10000
levy       = premiumTotal * centralFundBps / 10000
net        = premiumTotal - commission - levy
line_i     = floor(net * lineShareBps_i / 10000)
last line  = net - sum(previous line amounts)
```

The plan pays the broker's account, the central fund and each line. The line's credit
capability deposits into the syndicate claims purse. Conservation is exact:

```
commission + levy + sum(line credits) == premiumTotal
```

All arithmetic is integer minor units with a 10000 bps denominator. The last bucket absorbs
the rounding remainder; no dust is created or destroyed.

Premium is non-refundable after inception in v1. A slip that expires or is cancelled before
binding refunds the premium to the insured (design; the refund path is mapped but not yet
behaviourally tested).
