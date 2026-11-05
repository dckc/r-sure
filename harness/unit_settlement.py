#!/usr/bin/env python3
"""Settlement: payable, line payout, fund cover and policy aggregate."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("settlement"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("settle")

        A.cover('Policy@"payable"', "success")
        payable = actors.invoke(p.policy_uri, "payable", "500")
        A.expect("payable before settlement", payable, (True, 500))
        A.expect("payable is capped by per-claim",
                 actors.invoke(p.policy_uri, "payable", "5000")[1] <= p.per_claim, True)

        claim_id, claim_uri = p.open_claim(amount=500)
        p.classify_claim()
        p.assess_claim(500)
        p.agree_claim(500)

        A.cover('SureFund@"covered"', "refusal")
        A.expect_refusal("no central-fund cover for this claim", actors.invoke(
            p.component("component:fund"), "covered", f'"{claim_id}"'), "not covered")

        A.cover('Claim@"settle"', "success")
        A.expect("claim settles", p.settle_claim(), (True, 500))
        A.cover('Line@"pay"', "success")
        line = p.lines_info()[0]
        A.expect("line paid the claim", line.get("paid"), 500)
        A.expect("line records the claim", line.get("paidFor").get(claim_id), 500)

        A.cover('Policy@"settleClaim"', "success")
        policy = p.policy_info()
        A.expect("policy aggregate paid", policy.get("aggregatePaid"), 500)
        A.expect("policy aggregate remaining", policy.get("aggregateRemaining"), 4500)
        A.expect("policy claim settled", policy.get("claims").get(claim_id).get("status"),
                 "settled")

        A.cover('SureMath@"settlePlan"', "success")
        plan = actors.invoke(p.component("component:suremath"), "settlePlan",
                             f'500, [{{"uri": "line", "shareBps": 10000}}]')
        A.expect("settle plan sums to payable", plan[1][0].get("amount"), 500)

        A.cover('SureFund@"shortfalls"', "success")
        A.expect_ok("fund shortfalls", actors.invoke(
            p.component("component:fund"), "shortfalls"))
    except Exception as error:
        print(f"settlement suite failed: {error}", file=sys.stderr)
        A.finish("settlement")
        return 1
    return A.finish("settlement")


if __name__ == "__main__":
    raise SystemExit(main())
