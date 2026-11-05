#!/usr/bin/env python3
"""Policy: terms, lines, claims, payable and holder-only distribution."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("policy"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("policy")

        A.cover('Policy@"info"', "success")
        info = p.policy_info()
        A.expect("policy is active", info.get("status"), "active")
        A.expect("policy is distributed", info.get("distributed"), True)
        A.expect("policy insured", info.get("insured"), p.owner_id)

        A.cover('Policy@"terms"', "success")
        terms = actors.invoke(p.policy_uri, "terms")
        A.expect("terms match", terms[1].get("premiumTotal"), p.premium)
        A.expect("aggregate limit", terms[1].get("aggregateLimit"), p.aggregate)

        A.cover('Policy@"lines"', "success")
        lines = actors.invoke(p.policy_uri, "lines")
        A.expect("one line", len(lines[1]), 1)
        line_id = lines[1][0].get("lineId")
        A.cover('Policy@"line"', "success")
        A.expect("policy line", actors.invoke(p.policy_uri, "line", f'"{line_id}"')[1],
                 lines[1][0])
        A.cover('Policy@"line"', "refusal")
        A.expect_refusal("unknown policy line", actors.invoke(
            p.policy_uri, "line", '"lin:missing"'), "unknown line")

        A.cover('Policy@"claims"', "success")
        A.expect("no claims", actors.invoke(p.policy_uri, "claims"), (True, {}))
        A.cover('Policy@"claim"', "refusal")
        A.expect_refusal("unknown claim", actors.invoke(
            p.policy_uri, "claim", '"clm:missing"'), "unknown claim")

        A.cover('Policy@"payable"', "success")
        A.expect("payable", actors.invoke(p.policy_uri, "payable", "400"), (True, 400))

        A.cover('Policy@"distribute"', "refusal")
        A.expect_refusal("non-holder distribute", actors.invoke(
            p.policy_uri, "distribute", "*dId"), "not holder")
        A.cover('Policy@"expire"', "refusal")
        A.expect_refusal("policy not expired", actors.invoke(p.policy_uri, "expire"),
                         "not expired")
    except Exception as error:
        print(f"policy suite failed: {error}", file=sys.stderr)
        A.finish("policy")
        return 1
    return A.finish("policy")


if __name__ == "__main__":
    raise SystemExit(main())
