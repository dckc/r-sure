#!/usr/bin/env python3
"""r-gen oracle boundary: disabled adapter, factory refusals and dispute refusal."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("oracle"):
        print("not_run: devnet unavailable")
        return 2
    try:
        rgen = actors.resolve("component:rgen")

        A.cover('RgenAdapter@"health"', "refusal")
        A.expect_refusal("r-gen health disabled", actors.invoke(rgen, "health"),
                         "disabled")
        A.cover('RgenAdapter@"config"', "success")
        A.expect("r-gen config disabled", actors.invoke(rgen, "config")[1].get("enabled"),
                 False)
        A.cover('RgenAdapter@"oracleFactory"', "refusal")
        A.expect_refusal("oracle factory disabled", actors.invoke(
            rgen, "oracleFactory"), "rgen disabled")
        A.cover('RgenAdapter@"credentialFactory"', "refusal")
        A.expect_refusal("credential factory disabled", actors.invoke(
            rgen, "credentialFactory"), "rgen disabled")
        A.cover('RgenAdapter@"claimFactory"', "refusal")
        A.expect_refusal("claim factory disabled", actors.invoke(
            rgen, "claimFactory"), "rgen disabled")

        p = F.bound("oracle", syndicate_owner="deployer")
        claim_id, claim_uri = p.open_claim(amount=100)
        p.classify_claim()
        A.cover('Claim@"dispute"', "refusal")
        A.expect_refusal("dispute needs r-gen", actors.invoke(
            claim_uri, "dispute", '*dId, {}', key=p.insured), "oracle unavailable")
        A.expect("claim state stays live", p.claim_info().get("status"), "classified")
        A.expect("claim nonce unchanged", p.claim_info().get("nonce"), 1)
    except Exception as error:
        print(f"oracle suite failed: {error}", file=sys.stderr)
        A.finish("oracle")
        return 1
    return A.finish("oracle")


if __name__ == "__main__":
    raise SystemExit(main())
