#!/usr/bin/env python3
"""End-to-end reuse: an r-sure policy settles through the same cash-flow primitives."""

import sys

import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("integration_rshare"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("reuse-journey", syndicate_owner="deployer")
        A.cover('SlipFactory@"open"', "success")
        A.cover('PolicyFactory@"create"', "success")
        A.cover('LineFactory@"create"', "success")
        A.expect("policy active", p.policy_info().get("status"), "active")
        claim_id, claim_uri = p.open_claim(amount=100)
        p.classify_claim()
        p.assess_claim(100)
        p.agree_claim(100)
        p.settle_claim()
        A.cover('Policy@"settleClaim"', "success")
        A.expect("claim settled", p.claim_info().get("status"), "settled")
        A.expect("policy paid", p.policy_info().get("aggregatePaid"), 100)
        A.expect("line paid", p.lines_info()[0].get("paid"), 100)
    except Exception as error:
        print(f"integration_rshare suite failed: {error}", file=sys.stderr)
        A.finish("integration_rshare")
        return 1
    return A.finish("integration_rshare")


if __name__ == "__main__":
    raise SystemExit(main())
