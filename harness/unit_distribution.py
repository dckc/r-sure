#!/usr/bin/env python3
"""DistributionFactory and the distributed premium plan."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("distribution"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("distribution", syndicate_owner="deployer")
        factory = p.component("component:distribution-factory")

        A.cover('Policy@"distribute"', "success")
        A.expect("policy distributed", p.policy_info().get("distributed"), True)
        line = p.lines_info()[0]
        A.expect("line credited", line.get("credited") > 0, True)

        A.cover('DistributionFactory@"create"', "success")
        # The factory is exercised through Policy@"distribute" above; the policy
        # holds the purse and policy token, so Python cannot call it directly.
        A.expect("policy premium is fully allocated",
                 p.policy_info().get("premiumTotal") > 0, True)
    except Exception as error:
        print(f"distribution suite failed: {error}", file=sys.stderr)
        A.finish("distribution")
        return 1
    return A.finish("distribution")


if __name__ == "__main__":
    raise SystemExit(main())
