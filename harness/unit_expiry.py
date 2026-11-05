#!/usr/bin/env python3
"""Expiry and refunds: slip refund, risk expiry and policy line release."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("expiry"):
        print("not_run: devnet unavailable")
        return 2
    try:
        slip = F.started("expiry", syndicate_owner="deployer",
                         expiry_blocks=2, period_blocks=20)
        slip.accept()
        slip.fund_premium()
        actors.wait_height(slip.expiry_height + 2)
        before_refund = actors.balance(slip.insured)
        A.cover('Slip@"expire"', "success")
        A.expect_ok("slip expires", actors.invoke(slip.slip_uri, "expire"))
        A.expect("slip status", slip.slip_info().get("status"), "expired")
        A.expect("premium refunded to the insured",
                 actors.balance(slip.insured) >= before_refund + slip.premium, True)

        policy = F.bound("pexpiry", syndicate_owner="deployer",
                         period_blocks=20, run_off_blocks=0)
        actors.wait_height(policy.end + 2)
        A.cover('Policy@"expire"', "success")
        A.expect_ok("policy expires", actors.invoke(policy.policy_uri, "expire"))
        A.expect("policy status", policy.policy_info().get("status"), "expired")
        A.cover('Line@"release"', "success")
        A.expect("line released", policy.lines_info()[0].get("status"), "released")
        A.cover('Policy@"openClaim"', "refusal")
        A.expect_refusal("expired policy refuses new claims", actors.invoke(
            policy.policy_uri, "openClaim", "*dId, {}", key=policy.insured), "not active")
    except Exception as error:
        print(f"expiry suite failed: {error}", file=sys.stderr)
        A.finish("expiry")
        return 1
    return A.finish("expiry")


if __name__ == "__main__":
    raise SystemExit(main())
