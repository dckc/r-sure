#!/usr/bin/env python3
"""Variance is risk: the shared measure, the engineering/insurer gap and the load."""

import json
import sys

import actors
import assertions as A
import preflight

KASSET = "rho:id:variance-fixture-kasset"

REQ = {
    "class": "engineering",
    "broker": "broker-variance",
    "assetRef": {"kind": "property", "hash": "asset-variance", "uri": KASSET},
    "evidence": [
        {"kind": "survey", "hash": "survey-variance"},
        {"kind": "rgen:kasset", "uri": KASSET, "hash": "kasset-variance"},
    ],
    "variance": {"source": "attested", "kassetUri": KASSET,
                 "varianceBps": 1000, "evidenceHash": "kasset-variance"},
    "triTest": {
        "exposureRef": "exposure-variance",
        "probabilityBasis": "claims-history",
        "consequenceBasis": "declared-value",
        "consequenceRef": "consequence-variance",
    },
    "periodStart": 0,
    "periodEnd": 1_000_000,
    "declaredValue": 100_000,
    "requestedLimit": 50_000,
    "requestedDeductible": 1_000,
}


def assessment(insurer: int, premium: int = 1200, tolerance: int = 2000) -> dict:
    return {
        "quotedPremium": premium,
        "expectedLoss": 1000,
        "varianceBps": insurer,
        "loadBps": 2000,
        "basisHash": "underwriting:variance",
        "toleranceBps": tolerance,
    }


def submit(book: str, req: dict):
    return actors.invoke(book, "submit", f"*dId, {json.dumps(req)}")


def main() -> int:
    if not preflight.require_devnet("variance"):
        print("not_run: devnet unavailable")
        return 2
    try:
        math = actors.resolve("component:suremath")
        book = actors.resolve("component:risk-book")

        A.cover('SureMath@"varianceRate"', "success")
        A.expect("perfect quality has no measured variance",
                 actors.invoke(math, "varianceRate", '20, "valid"'),
                 (True, 0))
        A.expect("mid quality", actors.invoke(math, "varianceRate", '12, "valid"'),
                 (True, 4000))
        A.expect("partial verdict", actors.invoke(math, "varianceRate", '20, "partial"'),
                 (True, 1000))
        A.cover('SureMath@"varianceRate"', "refusal")
        A.expect_refusal("quality out of range",
                         actors.invoke(math, "varianceRate", '3, "valid"'), "quality")
        A.expect_refusal("unknown verdict",
                         actors.invoke(math, "varianceRate", '12, "invalid"'),
                         "verdict")

        A.cover('SureMath@"varianceGap"', "success")
        A.expect("wide gap is flagged",
                 actors.invoke(math, "varianceGap", "1000, 3000, 1000"),
                 (True, 2000, True))
        A.expect("within tolerance",
                 actors.invoke(math, "varianceGap", "1000, 1500, 1000"),
                 (True, 500, False))
        A.expect("negative gap",
                 actors.invoke(math, "varianceGap", "3000, 1000, 1000"),
                 (True, -2000, True))
        A.cover('SureMath@"varianceGap"', "refusal")
        A.expect_refusal("bad gap input",
                         actors.invoke(math, "varianceGap", "10001, 0, 0"), "bps")

        A.cover('SureMath@"loadedPremium"', "success")
        A.expect("variance-principle load",
                 actors.invoke(math, "loadedPremium", "1000, 5000, 2000"),
                 (True, 1100))
        A.expect("zero variance has no load",
                 actors.invoke(math, "loadedPremium", "1000, 0, 2000"),
                 (True, 1000))
        A.cover('SureMath@"loadedPremium"', "refusal")
        A.expect_refusal("variance out of range",
                         actors.invoke(math, "loadedPremium", "1000, 10001, 2000"),
                         "amount")

        A.cover('SureMath@"varianceStats"', "success")
        A.expect("two-point variance rate",
                 actors.invoke(math, "varianceStats", "[1000, 2000]"),
                 (True, 1111, 2000000))

        A.cover('RiskBook@"submit"', "success")
        created = submit(book, REQ)
        A.expect_ok("submit variance risk", created)
        risk_uri = created[2]

        A.cover('Risk@"assess"', "success")
        A.expect_ok("assess", actors.invoke(
            risk_uri, "assess", f"*dId, {json.dumps(assessment(2000))}"))
        A.cover('Risk@"variance"', "success")
        variable = actors.invoke(risk_uri, "variance")[1]
        A.expect("engineering estimate", variable.get("engineeringBps"), 1000)
        A.expect("insurer estimate", variable.get("insurerBps"), 2000)
        A.expect("signed gap", variable.get("gapBps"), 1000)
        A.expect("within tolerance is not flagged", variable.get("flagged"), False)
        A.expect("minimum premium", variable.get("minimumPremium"), 1040)

        A.cover('Risk@"accept"', "success")
        A.expect_ok("accept acknowledges", actors.invoke(risk_uri, "accept", "*dId"))
        A.expect("acknowledged on accept",
                 actors.invoke(risk_uri, "variance")[1].get("acknowledged"), True)

        flagged = submit(book, dict(REQ, broker="broker-variance-2"))
        A.expect_ok("submit flagged risk", flagged)
        flagged_uri = flagged[2]
        A.expect_ok("assess wide gap", actors.invoke(
            flagged_uri, "assess", f"*dId, {json.dumps(assessment(5000, tolerance=1000))}"))
        state = actors.invoke(flagged_uri, "variance")[1]
        A.expect("wide gap is visible", state.get("flagged"), True)
        A.expect("wide gap is signed", state.get("gapBps"), 4000)

        A.cover('Risk@"assess"', "refusal")
        bad = submit(book, dict(REQ, broker="broker-variance-3"))
        A.expect_refusal("variance out of range", actors.invoke(
            bad[2], "assess", f"*dId, {json.dumps(assessment(10001))}"), "assessment")
        A.expect_refusal("premium below floor", actors.invoke(
            bad[2], "assess", f"*dId, {json.dumps(assessment(2000, premium=1))}"),
            "premium floor")

        A.cover('RiskBook@"submit"', "refusal")
        wrong = dict(REQ, broker="broker-variance-4")
        wrong["variance"] = dict(REQ["variance"], evidenceHash="not-in-evidence")
        A.expect_refusal("attestation must bind to evidence", submit(book, wrong),
                         "attestation binding")

        A.cover('Risk@"accept"', "refusal")
        fresh = submit(book, dict(REQ, broker="broker-variance-5"))
        A.expect_refusal("accept before assess",
                         actors.invoke(fresh[2], "accept", "*dId"), "not assessed")
    except Exception as error:
        print(f"variance suite failed: {error}", file=sys.stderr)
        A.finish("variance")
        return 1
    return A.finish("variance")


if __name__ == "__main__":
    raise SystemExit(main())
