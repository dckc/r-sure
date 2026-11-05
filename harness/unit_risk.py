#!/usr/bin/env python3
"""RiskBook/Risk: submission, assessment, acceptance, evidence and refusals."""

import json
import sys

import actors
import assertions as A
import preflight


REQ = {
    "class": "engineering",
    "broker": "broker-1",
    "assetRef": {"kind": "property", "hash": "asset-hash"},
    "evidence": [{"kind": "survey", "hash": "evidence-hash"}],
    "triTest": {
        "exposureRef": "exposure-ref",
        "probabilityBasis": "probability-basis",
        "consequenceBasis": "consequence-basis",
        "consequenceRef": "consequence-ref",
    },
    "periodStart": 0,
    "periodEnd": 1_000_000,
    "declaredValue": 100_000,
    "requestedLimit": 50_000,
    "requestedDeductible": 1_000,
}

SUBMIT = """
new rl(`rho:registry:lookup`), ch, ret,
    dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{book}`, *ch) |
  for (RiskBook <- ch) {{
    RiskBook!("submit", *dId, {req}, *ret) |
    for (@r <- ret) {{ deployId!(r) }}
  }}
}}
"""

CALL = """
new rl(`rho:registry:lookup`), ch, ret,
    dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{risk}`, *ch) |
  for (Risk <- ch) {{
    Risk!("{binding}"{args}, *ret) |
    for (@r <- ret) {{ deployId!(r) }}
  }}
}}
"""


def submit(book: str, req: dict):
    return A.one(SUBMIT.format(book=book, req=json.dumps(req)), phlo_limit=4_000_000)


def call(risk: str, binding: str, args: str = ""):
    return A.one(CALL.format(risk=risk, binding=binding, args=args), phlo_limit=4_000_000)


def main() -> int:
    if not preflight.require_devnet("risk"):
        print("not_run: devnet unavailable")
        return 2
    try:
        book = actors.resolve("component:risk-book")

        A.cover('RiskBook@"submit"', "success")
        created = submit(book, REQ)
        A.expect_ok("submit risk", created)
        risk_id, risk_uri = created[1], created[2]

        A.cover('RiskBook@"risk"', "success")
        A.expect("risk lookup", actors.invoke(book, "risk", f'"{risk_id}"'),
                 (True, risk_uri))
        A.cover('RiskBook@"risks"', "success")
        A.expect_ok("risks", actors.invoke(book, "risks"))
        A.cover('RiskBook@"byInsured"', "success")
        by_insured = actors.invoke(book, "byInsured",
                                   f'"{actors.address("deployer")}"')
        A.expect("risk indexed by insured", risk_id in by_insured[1], True)

        A.cover('Risk@"info"', "success")
        info = call(risk_uri, "info")
        A.expect_ok("risk info", info)
        A.expect("risk starts submitted", info[1].get("status"), "submitted")

        A.cover('Risk@"evidence"', "success")
        A.expect_ok("risk evidence", call(risk_uri, "evidence"))

        A.cover('Risk@"addEvidence"', "success")
        call(risk_uri, "addEvidence",
             ', *dId, [{"kind": "photo", "hash": "evidence-2"}]')
        A.expect("add evidence grows the list",
                 len(call(risk_uri, "info")[1].get("evidence")), 2)

        A.cover('Risk@"assess"', "success")
        call(risk_uri, "assess",
             ', *dId, {"quotedPremium": 1200, "terms": "standard"}')
        A.expect("risk is assessed", call(risk_uri, "info")[1].get("status"), "assessed")

        A.cover('Risk@"accept"', "success")
        call(risk_uri, "accept", ", *dId")
        A.expect("risk is accepted", call(risk_uri, "info")[1].get("status"), "accepted")

        A.cover('RiskBook@"submit"', "refusal")
        A.expect_refusal("bad class", submit(book, dict(REQ, **{"class": "gambling"})),
                         "fields")
        missing = dict(REQ)
        missing.pop("assetRef")
        A.expect_refusal("missing asset", submit(book, missing), "fields")
        A.expect_refusal("bad period", submit(book, dict(REQ, periodStart=2_000_000)),
                         "terms")

        A.cover('RiskBook@"risk"', "refusal")
        A.expect_refusal("unknown risk", actors.invoke(book, "risk", '"rsk:missing"'),
                         "unknown risk")

        A.cover('Risk@"accept"', "refusal")
        # A fresh risk must be assessed before acceptance.
        fresh = submit(book, dict(REQ, **{"broker": "broker-2"}))
        A.expect_refusal("accept before assess", call(fresh[2], "accept", ", *dId"),
                         "not assessed")

        A.cover('Risk@"expire"', "refusal")
        A.expect_refusal("not expired", call(risk_uri, "expire"), "not expired")
    except Exception as error:
        print(f"risk suite failed: {error}", file=sys.stderr)
        A.finish("risk")
        return 1
    return A.finish("risk")


if __name__ == "__main__":
    raise SystemExit(main())
