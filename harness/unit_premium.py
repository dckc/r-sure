#!/usr/bin/env python3
"""Premium allocation: commission, central-fund levy and line credits conserve the premium."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("premium"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("premium", premium=1000, broker_bps=1000, fund_bps=250,
                    syndicate_owner="deployer")
        terms = p.policy_info().get("terms")
        premium = terms.get("premiumTotal")
        commission = premium * terms.get("brokerCommissionBps") // 10000
        levy = premium * terms.get("centralFundBps") // 10000

        A.cover('SureMath@"premiumSplit"', "success")
        split = actors.invoke(p.component("component:suremath"), "premiumSplit",
                              f"{premium}, {terms.get('brokerCommissionBps')}, "
                              f"{terms.get('centralFundBps')}")
        A.expect("premium split", split, (True, commission, levy, premium - commission - levy))

        A.cover('Policy@"distribute"', "success")
        A.expect("policy distributed", p.policy_info().get("distributed"), True)
        line = p.lines_info()[0]
        A.cover('Line@"credit"', "success")
        A.expect("line credited", line.get("credited"), premium - commission - levy)
        A.cover('SureFund@"contribute"', "success")
        fund = p.fund_info()
        A.expect("fund contribution", fund.get("contributions").get(p.policy_id), levy)
        A.expect("premium conserved",
                 commission + levy + line.get("credited"), premium)
        A.expect("fund balance at least the levy", fund.get("balance") >= levy, True)

        A.cover('SureMath@"lineShares"', "success")
        shares = actors.invoke(p.component("component:suremath"), "lineShares",
                               f"{premium - commission - levy}, "
                               '[{"uri": "line", "shareBps": 10000}]')
        A.expect("line shares conserve",
                 sum(item["amount"] for item in shares[1]), premium - commission - levy)
    except Exception as error:
        print(f"premium suite failed: {error}", file=sys.stderr)
        A.finish("premium")
        return 1
    return A.finish("premium")


if __name__ == "__main__":
    raise SystemExit(main())
