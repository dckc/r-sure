#!/usr/bin/env python3
"""Replay and one-shot guards across broker, slip, claim and admin paths."""

import sys

import actors
import admin
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("replay"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("replay", syndicate_owner="deployer")
        broker_book = p.component("component:broker-book")
        profile = {
            "name": "replay-broker",
            "licenceHash": "licence",
            "credentialUri": "rho:id:credential",
            "commissionBps": 1000,
            "classes": ["property"],
        }
        import json
        A.cover('BrokerBook@"register"', "refusal")
        A.expect_refusal("duplicate broker", actors.invoke(
            broker_book, "register", f"*dId, {json.dumps(profile)}", key=p.insured),
            "duplicate owner")

        A.cover('Slip@"bind"', "refusal")
        A.expect_refusal("duplicate bind", actors.invoke(p.slip_uri, "bind"), "closed")

        claim_id, claim_uri = p.open_claim(amount=100)
        p.classify_claim()
        p.assess_claim(100)
        p.agree_claim(100)
        A.cover('Claim@"settle"', "success")
        p.settle_claim()
        A.cover('Claim@"settle"', "refusal")
        A.expect_refusal("duplicate settlement", actors.invoke(claim_uri, "settle"),
                         "not agreed")

        admin_uri = actors.resolve("component:admin")
        keys = actors.keys()
        nonce = actors.invoke(admin_uri, "nonce")[1]
        sigs = admin.admin_sigs(keys, "admin", nonce + 1, "pauseAll")
        A.expect_ok("first pause", actors.invoke(
            admin_uri, "admin", f'{nonce + 1}, "pauseAll", [], {sigs}'))
        A.cover('SureAdmin@"admin"', "refusal")
        A.expect_refusal("admin nonce replay", actors.invoke(
            admin_uri, "admin", f'{nonce + 1}, "resumeAll", [], {sigs}'), "replay")
        resume = admin.admin_sigs(keys, "admin", nonce + 2, "resumeAll")
        A.expect_ok("resume", actors.invoke(
            admin_uri, "admin", f'{nonce + 2}, "resumeAll", [], {resume}'))
    except Exception as error:
        print(f"replay suite failed: {error}", file=sys.stderr)
        A.finish("replay")
        return 1
    return A.finish("replay")


if __name__ == "__main__":
    raise SystemExit(main())
