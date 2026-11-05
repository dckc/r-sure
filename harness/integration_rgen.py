#!/usr/bin/env python3
"""r-gen boundary: the adapter is either healthy or explicitly disabled."""

import sys

import actors
import assertions as A
import preflight


def main() -> int:
    if not preflight.require_devnet("integration_rgen"):
        print("not_run: devnet unavailable")
        return 2
    try:
        rgen = actors.resolve("component:rgen")
        health = actors.invoke(rgen, "health")
        config = actors.invoke(rgen, "config")
        A.cover('RgenAdapter@"health"', "success")
        A.cover('RgenAdapter@"config"', "success")
        A.expect_ok("adapter config", config)
        if health[0] is True:
            A.expect_ok("r-gen factories", health)
            A.expect("r-gen reports factories", "oracle" in health[1], True)
        else:
            A.expect_refusal("r-gen disabled by configuration", health, "disabled")
            A.expect("config records disabled", config[1].get("enabled"), False)
    except Exception as error:
        print(f"integration_rgen suite failed: {error}", file=sys.stderr)
        A.finish("integration_rgen")
        return 1
    return A.finish("integration_rgen")


if __name__ == "__main__":
    raise SystemExit(main())
