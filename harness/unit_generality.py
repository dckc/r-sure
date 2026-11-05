#!/usr/bin/env python3
"""CoverTerms and SureMath: validation, refusal and arithmetic conservation."""

import json
import sys

import actors
import assertions as A
import preflight


TERMS = {
    "coverageClass": "engineering",
    "assetId": "asset-1",
    "aggregateLimit": 1_000_000,
    "perClaimLimit": 500_000,
    "deductible": 1_000,
    "premiumTotal": 10_000,
    "periodStartHeight": 0,
    "periodEndHeight": 1_000,
    "waitingBlocks": 0,
    "noticeBlocks": 10,
    "runOffBlocks": 0,
    "standardClaimMax": 500_000,
    "minSyndicates": 1,
    "maxSyndicates": 4,
    "brokerCommissionBps": 1_000,
    "centralFundBps": 500,
    "evidencePolicy": "optional",
    "claimsLeadPolicy": "lead",
}


def terms(**overrides):
    value = dict(TERMS)
    for key, item in overrides.items():
        if item is None:
            value.pop(key, None)
        else:
            value[key] = item
    return json.dumps(value)


def main() -> int:
    if not preflight.require_devnet("generality"):
        print("not_run: devnet unavailable")
        return 2
    try:
        cover = actors.resolve("component:terms")
        math = actors.resolve("component:suremath")

        A.cover('CoverTerms@"fields"', "success")
        fields = actors.invoke(cover, "fields")
        A.expect("terms fields include aggregateLimit", "aggregateLimit" in fields, True)

        A.cover('CoverTerms@"validate"', "success")
        A.expect("valid terms accepted", actors.invoke(cover, "validate", terms()),
                 (True,))

        A.cover('CoverTerms@"validate"', "refusal")
        A.expect_refusal("missing class", actors.invoke(cover, "validate",
                         terms(coverageClass=None)), "class")
        A.expect_refusal("per-claim above aggregate", actors.invoke(cover, "validate",
                         terms(perClaimLimit=2_000_000)), "limits")
        A.expect_refusal("deductible at per-claim", actors.invoke(cover, "validate",
                         terms(deductible=500_000)), "deductible")
        A.expect_refusal("commission plus fund too high", actors.invoke(cover, "validate",
                         terms(brokerCommissionBps=3_000, centralFundBps=1)), "bps")
        A.expect_refusal("unknown evidence policy", actors.invoke(cover, "validate",
                         terms(evidencePolicy="sometimes")), "evidence")
        A.expect_refusal("unknown claims lead policy", actors.invoke(cover, "validate",
                         terms(claimsLeadPolicy="any")), "claims lead")

        A.cover('CoverTerms@"hash"', "success")
        digest = actors.invoke(cover, "hash", terms())
        A.expect_ok("terms hash", digest)
        A.expect("terms hash is stable", digest, actors.invoke(cover, "hash", terms()))

        A.cover('SureMath@"bpsSum"', "success")
        A.expect("bps sum",
                 actors.invoke(math, "bpsSum",
                               '[{"shareBps": 1000}, {"shareBps": 2000}]'),
                 (True, 3000))

        A.cover('SureMath@"share"', "success")
        A.expect("share conserves", actors.invoke(math, "share", "10000, 2500"),
                 (True, 2500, 7500))
        A.cover('SureMath@"share"', "refusal")
        A.expect_refusal("share rejects bps above 10000",
                         actors.invoke(math, "share", "10000, 10001"), "bps")

        A.cover('SureMath@"premiumSplit"', "success")
        A.expect("premium split conserves",
                 actors.invoke(math, "premiumSplit", "10000, 1000, 500"),
                 (True, 1000, 500, 8500))
        A.cover('SureMath@"premiumSplit"', "refusal")
        A.expect_refusal("premium split rejects bps sum",
                         actors.invoke(math, "premiumSplit", "10000, 6000, 5000"), "bps")

        lines = '[{"uri": "a", "shareBps": 5000}, {"uri": "b", "shareBps": 5000}]'
        short = '[{"uri": "a", "shareBps": 5000}, {"uri": "b", "shareBps": 4000}]'
        A.cover('SureMath@"lineExposures"', "success")
        exposures = actors.invoke(math, "lineExposures", f"1000000, {lines}")
        A.expect_ok("line exposures", exposures)
        A.expect("line exposures sum to aggregate",
                 sum(item["amount"] for item in exposures[1]), 1_000_000)
        A.cover('SureMath@"lineExposures"', "refusal")
        A.expect_refusal("line exposures require 10000 bps",
                         actors.invoke(math, "lineExposures", f"1000000, {short}"),
                         "shares")

        A.cover('SureMath@"lineShares"', "success")
        shares = actors.invoke(math, "lineShares", f"8500, {lines}")
        A.expect_ok("line shares", shares)
        A.expect("line shares conserve",
                 sum(item["amount"] for item in shares[1]), 8500)

        A.cover('SureMath@"payable"', "success")
        A.expect("payable applies deductible",
                 actors.invoke(math, "payable", "500000, 500000, 1000000, 1000"),
                 (True, 499_000))
        A.cover('SureMath@"payable"', "refusal")
        A.expect_refusal("payable rejects negative amount",
                         actors.invoke(math, "payable", "-1, 500000, 1000000, 1000"),
                         "amount")

        A.cover('SureMath@"settlePlan"', "success")
        plan = actors.invoke(math, "settlePlan", f"1000, {lines}")
        A.expect_ok("settle plan", plan)
        A.expect("settle plan sums to payable",
                 sum(item["amount"] for item in plan[1]), 1000)
    except Exception as error:
        print(f"generality suite failed: {error}", file=sys.stderr)
        A.finish("generality")
        return 1
    return A.finish("generality")


if __name__ == "__main__":
    raise SystemExit(main())
