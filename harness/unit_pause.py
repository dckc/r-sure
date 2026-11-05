#!/usr/bin/env python3
"""Global pause: new risk is blocked while claims and reads stay available."""

import sys

import actors
import admin
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("pause"):
        print("not_run: devnet unavailable")
        return 2
    try:
        admin_uri = actors.resolve("component:admin")
        keys = actors.keys()
        if actors.invoke(admin_uri, "isPaused")[1]:
            current = actors.invoke(admin_uri, "nonce")[1]
            unlock = admin.admin_sigs(keys, "admin", current + 1, "resumeAll")
            actors.invoke(admin_uri, "admin",
                          f'{current + 1}, "resumeAll", [], {unlock}')
        p = F.bound("pause", syndicate_owner="deployer")
        start = actors.invoke(admin_uri, "nonce")[1]
        pause_sigs = admin.admin_sigs(keys, "admin", start + 1, "pauseAll")
        A.expect_ok("pauseAll", actors.invoke(
            admin_uri, "admin", f'{start + 1}, "pauseAll", [], {pause_sigs}'))
        A.expect("paused", actors.invoke(admin_uri, "isPaused"), (True, True))

        A.cover('SyndicateBook@"create"', "refusal")
        profile = {"name": "paused", "assetId": "REV", "riskAppetite": ["property"]}
        A.expect_refusal("new syndicate blocked", actors.invoke(
            p.component("component:syndicate-book"), "create",
            f"*dId, {__import__('json').dumps(profile)}", key="deployer"), "paused")

        A.cover('RiskBook@"submit"', "refusal")
        A.expect_refusal("new risk blocked", actors.invoke(
            p.component("component:risk-book"), "submit", "*dId, {}", key=p.insured),
            "paused")

        A.cover('Policy@"openClaim"', "success")
        claim_id, claim_uri = p.open_claim(amount=100)
        A.expect("claims remain available while paused", claim_id.startswith("clm:"), True)
        A.cover('Policy@"info"', "success")
        A.expect_ok("policy reads remain available", actors.invoke(p.policy_uri, "info"))

        resume_sigs = admin.admin_sigs(keys, "admin", start + 2, "resumeAll")
        A.expect_ok("resumeAll", actors.invoke(
            admin_uri, "admin", f'{start + 2}, "resumeAll", [], {resume_sigs}'))
        A.expect("resumed", actors.invoke(admin_uri, "isPaused"), (True, False))
    except Exception as error:
        print(f"pause suite failed: {error}", file=sys.stderr)
        A.finish("pause")
        return 1
    return A.finish("pause")


if __name__ == "__main__":
    raise SystemExit(main())
