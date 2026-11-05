#!/usr/bin/env python3
"""Shortfall and aggregate exhaustion: payable caps and policy exhaustion refusal."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("shortfall"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("short", aggregate=2000, per_claim=500, premium=1000,
                    syndicate_owner="deployer", capital=3000)

        A.cover('Policy@"payable"', "success")
        A.expect("payable is capped by per-claim",
                 actors.invoke(p.policy_uri, "payable", "5000"), (True, 500))
        A.expect("payable is capped by aggregate",
                 actors.invoke(p.policy_uri, "payable", "5000")[1] <= 2000, True)

        paid = []
        for index in range(4):
            claim_id, claim_uri = p.open_claim(amount=1000)
            p.classify_claim()
            p.assess_claim(1000)
            p.agree_claim(1000)
            A.cover('Claim@"settle"', "success")
            reply = p.settle_claim()
            paid.append(reply[1])
            A.expect(f"claim {index} pays the per-claim cap", reply[1], 500)

        A.cover('Policy@"openClaim"', "refusal")
        A.expect_refusal("aggregate exhausted", actors.invoke(
            p.policy_uri, "openClaim",
            f'*dId, {{"lossHeight": {p.end - 1}, "claimedAmount": 100, '
            f'"evidence": [{{"kind": "loss", "hash": "h"}}]}}',
            key=p.insured), "exhausted")
        A.expect("aggregate is exhausted", p.policy_info().get("aggregateRemaining"), 0)
        A.expect("payments never exceed the aggregate", sum(paid), 2000)

        A.cover('SureFund@"shortfalls"', "success")
        A.expect_ok("fund shortfalls", actors.invoke(
            p.component("component:fund"), "shortfalls"))
        A.cover('SureFund@"balance"', "success")
        A.expect_ok("fund balance", actors.invoke(
            p.component("component:fund"), "balance"))
    except Exception as error:
        print(f"shortfall suite failed: {error}", file=sys.stderr)
        A.finish("shortfall")
        return 1
    return A.finish("shortfall")


if __name__ == "__main__":
    raise SystemExit(main())
