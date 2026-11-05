#!/usr/bin/env python3
"""Payments: r-cash health, account, issuer and deposit-facet reply shapes."""

import sys

import actors
import assertions as A
import preflight


ENSURE_TERM = """
new rl(`rho:registry:lookup`), ch, ret,
    dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{payments}`, *ch) |
  for (Payments <- ch) {{
    Payments!("ensureAccount", *dId, *ret) |
    for (@r <- ret) {{ deployId!(r) }}
  }}
}}
"""


def main() -> int:
    if not preflight.require_devnet("payments"):
        print("not_run: devnet unavailable")
        return 2
    try:
        uri = A.component_uri("40_payments.rho")
        owner = actors.address("deployer")

        A.cover('Payments@"health"', "success")
        health = A.one(A.call(uri, "health"))
        A.expect_ok("health", health)
        A.expect("health reports both rails",
                 sorted(health[1].keys()), ["accountFactory", "assetResolver", "clock"])

        A.cover('Payments@"accountOf"', "success")
        account = A.one(A.call(uri, "accountOf", f'"{owner}"'))
        A.expect_ok("accountOf", account)
        A.expect("accountOf has an account capability", len(account), 2)

        A.cover('Payments@"depositFacet"', "success")
        facet = A.one(A.call(uri, "depositFacet", f'"{owner}", "REV"'))
        A.expect_ok("depositFacet", facet)

        A.cover('Payments@"issuer"', "success")
        issuer = A.one(A.call(uri, "issuer", '"REV"'))
        A.expect_ok("issuer REV", issuer)
        A.expect("issuer reply has brand and issuer", len(issuer), 3)

        A.cover('Payments@"issuer"', "refusal")
        A.expect_refusal("issuer unknown asset",
                         A.one(A.call(uri, "issuer", '"NOT-AN-ASSET"')), "asset")

        A.cover('Payments@"ensureAccount"', "success")
        ensured = A.one(ENSURE_TERM.format(payments=uri), phlo_limit=2_000_000)
        A.expect_ok("ensureAccount", ensured)
        A.expect("ensureAccount reply has account and owner", len(ensured), 3)

        A.cover('Payments@"platformOwner"', "success")
        platform = A.one(A.call(uri, "platformOwner"))
        A.expect_ok("platformOwner", platform)
    except Exception as error:
        print(f"payments suite failed: {error}", file=sys.stderr)
        A.finish("payments")
        return 1
    return A.finish("payments")


if __name__ == "__main__":
    raise SystemExit(main())
