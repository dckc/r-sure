#!/usr/bin/env python3
"""Reusable interfaces: a policy and its line behave as general cash-flow primitives."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("share_reuse"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("reuse", syndicate_owner="deployer")
        payments = p.component("component:payments")
        owner = p.owner_id

        A.cover('Payments@"accountOf"', "success")
        A.expect_ok("reusable account lookup", actors.invoke(
            payments, "accountOf", f'"{owner}"'))
        A.cover('Payments@"depositFacet"', "success")
        A.expect_ok("reusable deposit facet", actors.invoke(
            payments, "depositFacet", f'"{owner}", "REV"'))

        A.cover('Policy@"info"', "success")
        A.expect("bound policy is a reusable value", p.policy_info().get("status"), "active")
        A.cover('Line@"info"', "success")
        line = p.line_uri(p.policy_lines()[0]["lineId"])
        A.expect_ok("line is a reusable capability", actors.invoke(line, "info"))

        claim_id, claim_uri = p.open_claim(amount=100)
        p.classify_claim()
        p.assess_claim(100)
        p.agree_claim(100)
        p.settle_claim()
        A.cover('Claim@"settle"', "success")
        A.expect("reused policy pays", p.line_info(line).get("paid"), 100)
    except Exception as error:
        print(f"share_reuse suite failed: {error}", file=sys.stderr)
        A.finish("share_reuse")
        return 1
    return A.finish("share_reuse")


if __name__ == "__main__":
    raise SystemExit(main())
