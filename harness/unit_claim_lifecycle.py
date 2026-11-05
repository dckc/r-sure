#!/usr/bin/env python3
"""Claim lifecycle: notify, classify, assess, agree, settle and close."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("claim_lifecycle"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("claimlife")

        A.cover('Policy@"openClaim"', "success")
        claim_id, claim_uri = p.open_claim(amount=500)
        A.expect("claim notified", p.claim_info().get("status"), "notified")
        A.expect("claim id is stable", p.claim_info().get("id"), claim_id)
        A.expect("policy records the claim", claim_id in p.policy_info().get("claims"), True)

        A.cover('Claim@"info"', "success")
        A.expect_ok("claim info", actors.invoke(claim_uri, "info"))
        A.cover('Claim@"evidence"', "success")
        A.expect_ok("claim evidence", actors.invoke(claim_uri, "evidence"))
        A.cover('Claim@"addEvidence"', "success")
        actors.invoke(claim_uri, "addEvidence",
                      f"*dId, [{{\"kind\": \"photo\", \"hash\": \"evidence-2\"}}]",
                      key=p.insured)
        A.expect("evidence appended", len(p.claim_info().get("evidence")), 2)

        A.cover('Claim@"classify"', "success")
        A.expect_ok("classify", p.classify_claim())
        A.expect("classified", p.claim_info().get("status"), "classified")
        A.expect("classification", p.claim_info().get("classification", {}).get("kind"), "standard")

        A.cover('Claim@"assess"', "success")
        A.expect_ok("assess", p.assess_claim(500))
        A.expect("assessed", p.claim_info().get("status"), "assessed")
        A.expect("assessment recorded", p.claim_info().get("assessment", {}).get("recommendedAmount"), 500)

        A.cover('Claim@"agree"', "success")
        A.expect_ok("agree", p.agree_claim(500))
        A.expect("agreed", p.claim_info().get("status"), "agreed")
        A.expect("agreed amount", p.claim_info().get("agreedAmount"), 500)

        A.cover('Claim@"settle"', "success")
        A.expect("settle", p.settle_claim(), (True, 500))
        A.expect("settled", p.claim_info().get("status"), "settled")
        A.expect("paid amount", p.claim_info().get("paid"), 500)
        A.expect("policy aggregate paid", p.policy_info().get("aggregatePaid"), 500)
        A.expect("policy aggregate remaining", p.policy_info().get("aggregateRemaining"), 4500)

        A.cover('Claim@"close"', "success")
        A.expect_ok("close", p.close_claim())
        A.expect("closed", p.claim_info().get("status"), "closed")
        A.expect("line paid", p.lines_info()[0].get("paid"), 500)
        A.expect("policy claim is settled",
                 p.policy_info().get("claims").get(claim_id).get("status"), "settled")
    except Exception as error:
        print(f"claim_lifecycle suite failed: {error}", file=sys.stderr)
        A.finish("claim_lifecycle")
        return 1
    return A.finish("claim_lifecycle")


if __name__ == "__main__":
    raise SystemExit(main())
