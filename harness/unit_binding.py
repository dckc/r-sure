#!/usr/bin/env python3
"""Slip binding: full subscription, policy creation, line opening and one-shot bind."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("binding"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.started("binding", syndicate_owner="deployer")

        A.cover('Slip@"accept"', "success")
        A.expect_ok("accept", p.accept())
        A.cover('Slip@"subscribe"', "success")
        p.subscribe()
        A.cover('Slip@"fundPremium"', "success")
        A.expect("fund the exact premium", p.fund_premium(), p.premium)
        A.expect("fully funded", p.slip_info().get("funded"), p.premium)

        A.cover('Slip@"bind"', "success")
        policy_uri = p.bind()
        A.expect("slip bound", p.slip_info().get("status"), "bound")
        A.expect("policy URI", policy_uri.startswith("rho:id:"), True)
        A.cover('PolicyFactory@"create"', "success")
        A.expect("policy created", p.policy_info().get("id"), f"pol:{p.slip_id}")
        A.cover('LineFactory@"create"', "success")
        A.expect("one line created", len(p.policy_lines()), 1)
        A.cover('Slip@"bind"', "refusal")
        A.expect_refusal("bind is one-shot", actors.invoke(p.slip_uri, "bind"),
                         "closed")
        A.cover('Slip@"policy"', "success")
        A.expect("slip points at the policy", actors.invoke(p.slip_uri, "policy"),
                 (True, policy_uri))
    except Exception as error:
        print(f"binding suite failed: {error}", file=sys.stderr)
        A.finish("binding")
        return 1
    return A.finish("binding")


if __name__ == "__main__":
    raise SystemExit(main())
