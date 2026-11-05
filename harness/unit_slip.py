#!/usr/bin/env python3
"""SlipFactory/Slip: open, accept, subscribe, fund, bind and expiry guards."""

import json
import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("slip"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.started("slip", syndicate_owner="deployer")
        actors.ensure_vault("admin1")

        A.cover('SlipFactory@"open"', "success")
        info = p.slip_info()
        A.expect("slip starts open", info.get("status"), "open")
        A.expect("slip owner", info.get("insured"), p.owner_id)

        A.cover('Slip@"info"', "success")
        A.expect_ok("slip info", actors.invoke(p.slip_uri, "info"))
        A.cover('Slip@"premium"', "success")
        premium = actors.invoke(p.slip_uri, "premium")
        A.expect("premium total", premium[1].get("total"), p.premium)
        A.expect("premium funded starts at zero", premium[1].get("funded"), 0)
        A.cover('Slip@"policy"', "success")
        A.expect("no policy before bind", actors.invoke(p.slip_uri, "policy"), (True,))

        A.cover('Slip@"accept"', "refusal")
        A.expect_refusal("non-insured accept",
                         actors.invoke(p.slip_uri, "accept", "*dId", key="admin1"),
                         "not insured")
        A.cover('Slip@"accept"', "success")
        A.expect_ok("insured accept", p.accept())

        A.cover('Slip@"subscribe"', "success")
        p.subscribe()
        A.cover('Slip@"subscriptions"', "success")
        subs = actors.invoke(p.slip_uri, "subscriptions")
        A.expect("one subscription", len(subs[1]), 1)
        A.cover('Slip@"subscription"', "success")
        A.expect_ok("subscription", actors.invoke(
            p.slip_uri, "subscription", json.dumps(p.syndicate_id)))
        A.cover('Slip@"subscribe"', "refusal")
        A.expect_refusal("duplicate syndicate", actors.invoke(
            p.slip_uri, "subscribe",
            f'*dId, "{p.syndicate_uri}", 100', key=p.insured),
            "duplicate syndicate")

        A.cover('Slip@"bind"', "refusal")
        A.expect_refusal("bind before funding", actors.invoke(p.slip_uri, "bind"),
                         "not funded")

        A.cover('Slip@"fundPremium"', "refusal")
        A.expect_refusal("non-insured funding", actors.invoke(
            p.slip_uri, "fundPremium", "*dId, \"dummy\"", key="admin1"),
            "not insured")

        A.cover('Slip@"bind"', "success")
        p.fund_premium()
        policy_uri = p.bind()
        A.expect("slip bound", p.slip_info().get("status"), "bound")
        A.expect("bind returns policy", policy_uri.startswith("rho:id:"), True)
        A.expect("slip stores policy", p.slip_info().get("policyUri"), policy_uri)

        A.cover('Slip@"expire"', "refusal")
        A.expect_refusal("bound slip does not expire", actors.invoke(p.slip_uri, "expire"),
                         "closed")

        A.cover('SlipFactory@"open"', "refusal")
        A.expect_refusal("missing risk", actors.invoke(
            p.component("component:slip-factory"), "open", "*dId, {}"), "broker unavailable")
    except Exception as error:
        print(f"slip suite failed: {error}", file=sys.stderr)
        A.finish("slip")
        return 1
    return A.finish("slip")


if __name__ == "__main__":
    raise SystemExit(main())
