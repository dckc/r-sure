#!/usr/bin/env python3
"""Live r-cash rail: root, account factory, REV issuer and deposit facet."""

import sys

import actors
import assertions as A
import preflight


def main() -> int:
    if not preflight.require_devnet("integration_rcash"):
        print("not_run: devnet unavailable")
        return 2
    try:
        root = actors.rcash_root_uri()
        A.cover('Payments@"health"', "success")
        payments = actors.resolve("component:payments")
        health = actors.invoke(payments, "health")
        A.expect_ok("r-cash rail health", health)

        owner = actors.ensure_account("deployer")
        A.cover('Payments@"accountOf"', "success")
        A.expect_ok("account", actors.invoke(payments, "accountOf", f'"{owner}"'))
        A.cover('Payments@"issuer"', "success")
        issuer = actors.invoke(payments, "issuer", '"REV"')
        A.expect_ok("REV issuer", issuer)
        A.cover('Payments@"depositFacet"', "success")
        A.expect_ok("deposit facet", actors.invoke(
            payments, "depositFacet", f'"{owner}", "REV"'))
        A.expect("r-cash root is a URI", root.startswith("rho:id:"), True)
    except Exception as error:
        print(f"integration_rcash suite failed: {error}", file=sys.stderr)
        A.finish("integration_rcash")
        return 1
    return A.finish("integration_rcash")


if __name__ == "__main__":
    raise SystemExit(main())
