#!/usr/bin/env python3
"""Evidence: risk/claim evidence append and the disabled r-gen boundary."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("evidence"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("evidence", syndicate_owner="deployer")
        rgen = actors.resolve("component:rgen")

        A.cover('Risk@"evidence"', "success")
        A.expect_ok("risk evidence", actors.invoke(p.risk_uri, "evidence"))
        A.cover('Risk@"addEvidence"', "success")
        actors.invoke(p.risk_uri, "addEvidence",
                      '*dId, [{"kind": "survey", "hash": "risk-evidence-2"}]',
                      key=p.insured)
        A.expect("risk evidence appended",
                 len(actors.invoke(p.risk_uri, "evidence")[1]), 2)

        claim_id, claim_uri = p.open_claim(amount=100)
        A.cover('Claim@"evidence"', "success")
        A.expect_ok("claim evidence", actors.invoke(claim_uri, "evidence"))
        A.cover('Claim@"addEvidence"', "success")
        actors.invoke(claim_uri, "addEvidence",
                      '*dId, [{"kind": "photo", "hash": "claim-evidence-2"}]',
                      key=p.insured)
        A.expect("claim evidence appended",
                 len(actors.invoke(claim_uri, "evidence")[1]), 2)

        A.cover('RgenAdapter@"health"', "refusal")
        A.expect_refusal("r-gen disabled", actors.invoke(rgen, "health"), "disabled")
        A.cover('RgenAdapter@"config"', "success")
        config = actors.invoke(rgen, "config")
        A.expect_ok("r-gen config", config)
        A.expect("r-gen disabled by boundary", config[1].get("enabled"), False)
        A.cover('RgenAdapter@"verifyClaim"', "refusal")
        A.expect_refusal("r-gen claim verification disabled",
                         actors.invoke(rgen, "verifyClaim", '"rho:id:claim"'),
                         "rgen disabled")
        A.cover('RgenAdapter@"verifyCredential"', "refusal")
        A.expect_refusal("r-gen credential verification disabled",
                         actors.invoke(rgen, "verifyCredential", '"rho:id:credential"'),
                         "rgen disabled")
    except Exception as error:
        print(f"evidence suite failed: {error}", file=sys.stderr)
        A.finish("evidence")
        return 1
    return A.finish("evidence")


if __name__ == "__main__":
    raise SystemExit(main())
