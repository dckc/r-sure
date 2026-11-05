#!/usr/bin/env python3
"""Factories refuse malformed or unauthorised construction requests."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("factory_auth"):
        print("not_run: devnet unavailable")
        return 2
    try:
        r = F.started_refusals("factories", actor="sender")

        A.cover('SlipFactory@"open"', "refusal")
        A.expect_refusal("unregistered broker", r.invoke(
            r.component("component:slip-factory"), "open", "*dId, {}"),
            "broker unavailable")
        A.cover('BrokerBook@"register"', "refusal")
        A.expect_refusal("bad broker profile", r.invoke(
            r.component("component:broker-book"), "register", "*dId, {}"), "profile")
        A.cover('SyndicateBook@"create"', "refusal")
        A.expect_refusal("bad syndicate profile", r.invoke(
            r.component("component:syndicate-book"), "create", "*dId, {}"), "profile")
        A.cover('RiskBook@"submit"', "refusal")
        A.expect_refusal("bad risk", r.invoke(
            r.component("component:risk-book"), "submit", "*dId, {}"), "fields")
        A.cover('PolicyFactory@"create"', "refusal")
        A.expect_refusal("bad policy", r.invoke(
            r.component("component:policy-factory"), "create",
            '{}, "dummy", "dummy", *dId, *dId'), "fields")
        A.cover('ClaimFactory@"create"', "refusal")
        A.expect_refusal("bad claim", r.invoke(
            r.component("component:claim-factory"), "create",
            '*dId, "rho:id:x", "pol:x", "ins", "brk", *dId, {}'), "fields")
        A.cover('LineFactory@"create"', "refusal")
        A.expect_refusal("bad line", r.invoke(
            r.component("component:line-factory"), "create",
            '{}, *dId, *dId, *dId, *dId'), "line")
    except Exception as error:
        print(f"factory_auth suite failed: {error}", file=sys.stderr)
        A.finish("factory_auth")
        return 1
    return A.finish("factory_auth")


if __name__ == "__main__":
    raise SystemExit(main())
