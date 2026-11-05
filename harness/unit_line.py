#!/usr/bin/env python3
"""Line: state, remaining, paidFor, credit/pay/release token guards and payout."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("line"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("line", syndicate_owner="deployer")
        line = p.line_uri(p.policy_lines()[0]["lineId"])

        A.cover('Line@"info"', "success")
        info = p.line_info(line)
        A.expect("line status", info.get("status"), "bound")
        A.expect("line has exposure", info.get("exposure") >= p.aggregate, True)
        A.cover('Line@"remaining"', "success")
        remaining = actors.invoke(line, "remaining")
        A.expect("remaining equals exposure before pay",
                 remaining, (True, info.get("exposure")))
        A.cover('Line@"paidFor"', "refusal")
        A.expect_refusal("claim not paid", actors.invoke(
            line, "paidFor", '"clm:missing"'), "not paid")

        A.cover('Line@"credit"', "refusal")
        A.expect_refusal("credit wrong token", actors.invoke(
            line, "credit", "*dId, \"dummy\""), "not holder")
        A.cover('Line@"pay"', "refusal")
        A.expect_refusal("pay wrong token", actors.invoke(
            line, "pay", '*dId, "clm:x", 1, "owner"'), "not holder")
        A.cover('Line@"release"', "refusal")
        A.expect_refusal("release wrong token", actors.invoke(
            line, "release", "*dId"), "not holder")

        claim_id, claim_uri = p.open_claim(amount=100)
        p.classify_claim()
        p.assess_claim(100)
        p.agree_claim(100)
        p.settle_claim()
        A.cover('Line@"pay"', "success")
        paid = p.line_info(line)
        A.expect("line paid the claim", paid.get("paid"), 100)
        A.cover('Line@"paidFor"', "success")
        A.expect("paidFor", actors.invoke(line, "paidFor", f'"{claim_id}"'), (True, 100))
        A.cover('Line@"remaining"', "success")
        A.expect("remaining decreases", actors.invoke(line, "remaining")[1],
                 info.get("exposure") - 100)
    except Exception as error:
        print(f"line suite failed: {error}", file=sys.stderr)
        A.finish("line")
        return 1
    return A.finish("line")


if __name__ == "__main__":
    raise SystemExit(main())
