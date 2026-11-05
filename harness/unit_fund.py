#!/usr/bin/env python3
"""SureFund: balance, contributions, covers, shortfalls and admin refusal."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("fund"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("fund", syndicate_owner="deployer")
        fund = p.component("component:fund")

        A.cover('SureFund@"info"', "success")
        info = actors.invoke(fund, "info")
        A.expect_ok("fund info", info)
        A.expect("fund asset", info[1].get("assetId"), "REV")
        A.cover('SureFund@"balance"', "success")
        balance = actors.invoke(fund, "balance")
        A.expect("fund balance", balance[1] >= 0, True)

        A.cover('SureFund@"contribute"', "success")
        before = actors.invoke(fund, "balance")[1]
        A.expect_ok("contribute to fund",
                    actors.contribute_fund(fund, 10, p.policy_id, key=p.insured))
        after = actors.invoke(fund, "balance")[1]
        A.expect("fund balance increases", after, before + 10)
        A.expect("contribution is booked",
                 p.fund_info().get("contributions").get(p.policy_id) >= 10, True)

        A.cover('SureFund@"covered"', "refusal")
        A.expect_refusal("no cover", actors.invoke(fund, "covered", '"clm:missing"'),
                         "not covered")
        A.cover('SureFund@"shortfalls"', "success")
        A.expect_ok("shortfalls", actors.invoke(fund, "shortfalls"))

        A.cover('SureFund@"admin"', "refusal")
        A.expect_refusal("admin below threshold", actors.invoke(
            fund, "admin", "1, \"setCover\", [], []"), "below threshold")
    except Exception as error:
        print(f"fund suite failed: {error}", file=sys.stderr)
        A.finish("fund")
        return 1
    return A.finish("fund")


if __name__ == "__main__":
    raise SystemExit(main())
