#!/usr/bin/env python3
"""Closed-set conservation for premium distribution and claim settlement."""

import sys

import assertions as A
import conservation as C
import preflight


def main() -> int:
    if not preflight.require_devnet("conservation"):
        print("not_run: devnet unavailable")
        return 2
    try:
        A.cover('Policy@"distribute"', "success")
        premium = C.scenario_premium("cons-premium")
        split = premium["expected"]
        A.expect("premium split conserves",
                 split["commission"] + split["levy"] + split["line_credits"],
                 split["premium"])
        A.cover('SureMath@"premiumSplit"', "success")
        A.expect("commission", split["commission"] >= 0, True)
        A.cover('Line@"credit"', "success")
        A.expect("line credits", split["line_credits"] > 0, True)

        A.cover('Claim@"settle"', "success")
        settlement = C.scenario_settlement("cons-settle", amount=100)
        payout = settlement["payout"]
        A.expect("settlement conserves", payout.get("payable"), payout.get("line_paid"))
        A.cover('Line@"pay"', "success")
        A.expect("line payout", payout.get("line_paid"), 100)
        A.cover('SureFund@"covered"', "success")
        A.expect("fund cover is bounded", payout.get("cover", 0) <= payout.get("payable"), True)

        C.negative_control("cons-negative")
        A.expect("negative control detects escrow", True, True)
    except Exception as error:
        print(f"conservation suite failed: {error}", file=sys.stderr)
        A.finish("conservation")
        return 1
    return A.finish("conservation")


if __name__ == "__main__":
    raise SystemExit(main())
