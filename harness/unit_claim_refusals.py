#!/usr/bin/env python3
"""Claim and policy refusal paths: window, authority, terminal states and malformed input."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("claim_refusals"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("claimref")
        actors.ensure_vault("admin1")

        A.cover('Policy@"openClaim"', "refusal")
        A.expect_refusal("non-insured cannot notify", actors.invoke(
            p.policy_uri, "openClaim", "*dId, {}", key="admin1"), "not insured")
        A.expect_refusal("loss before period", actors.invoke(
            p.policy_uri, "openClaim",
            f'*dId, {{"lossHeight": 0, "claimedAmount": 100, "evidence": []}}',
            key=p.insured), "notice")
        A.expect_refusal("loss after notice", actors.invoke(
            p.policy_uri, "openClaim",
            f'*dId, {{"lossHeight": {p.end + 10000}, "claimedAmount": 100, "evidence": []}}',
            key=p.insured), "notice")
        A.expect_refusal("zero claim", actors.invoke(
            p.policy_uri, "openClaim",
            '*dId, {"lossHeight": 1, "claimedAmount": 0, "evidence": []}',
            key=p.insured), "amount")

        claim_id, claim_uri = p.open_claim(amount=500)
        A.cover('Claim@"settle"', "refusal")
        A.expect_refusal("settle before agreement", actors.invoke(claim_uri, "settle"),
                         "not agreed")
        A.cover('Claim@"assess"', "refusal")
        A.expect_refusal("assess before classification", actors.invoke(
            claim_uri, "assess", '*dId, {"recommendedAmount": 100}', key=p.insured),
            "not manager")

        p.classify_claim()
        A.cover('Claim@"agree"', "refusal")
        A.expect_refusal("non-lead cannot agree", actors.invoke(
            claim_uri, "agree", '*dId, 100, "basis"', key="admin1"), "not lead")
        p.assess_claim(500)
        p.agree_claim(500)
        p.settle_claim()
        A.cover('Claim@"agree"', "refusal")
        A.expect_refusal("terminal agree", actors.invoke(
            claim_uri, "agree", '*dId, 100, "basis"', key=p.insured), "closed")
        A.cover('Claim@"addEvidence"', "refusal")
        A.expect_refusal("terminal evidence", actors.invoke(
            claim_uri, "addEvidence", "*dId, []", key=p.insured), "closed")
        A.cover('Claim@"classify"', "refusal")
        A.expect_refusal("terminal classify", actors.invoke(
            claim_uri, "classify", '*dId, "standard"', key=p.insured), "closed")
        A.cover('Claim@"settle"', "refusal")
        A.expect_refusal("settle twice", actors.invoke(claim_uri, "settle"), "not agreed")

        A.cover('Policy@"claim"', "refusal")
        A.expect_refusal("unknown policy claim", actors.invoke(
            p.policy_uri, "claim", '"clm:missing"'), "unknown claim")
        A.cover('ClaimBook@"claim"', "refusal")
        A.expect_refusal("unknown book claim", actors.invoke(
            p.component("component:claim-book"), "claim", '"clm:missing"'),
            "unknown claim")
    except Exception as error:
        print(f"claim_refusals suite failed: {error}", file=sys.stderr)
        A.finish("claim_refusals")
        return 1
    return A.finish("claim_refusals")


if __name__ == "__main__":
    raise SystemExit(main())
