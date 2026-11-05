#!/usr/bin/env python3
"""BrokerBook/Broker: registration, profile, lookup, addSlip and refusals."""

import json
import sys

import actors
import assertions as A
import preflight


REGISTER = """
new rl(`rho:registry:lookup`), ch, ret,
    dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{book}`, *ch) |
  for (BrokerBook <- ch) {{
    BrokerBook!("register", *dId, {profile}, *ret) |
    for (@r <- ret) {{ deployId!(r) }}
  }}
}}
"""

ADD_SLIP = """
new rl(`rho:registry:lookup`), ch, ret,
    dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{broker}`, *ch) |
  for (Broker <- ch) {{
    Broker!("addSlip", *dId, "{slip_id}", "rho:id:test-slip", *ret) |
    for (@r <- ret) {{ deployId!(r) }}
  }}
}}
"""

PROFILE = {
    "name": "Test Broker",
    "licenceHash": "licence-hash",
    "credentialUri": "rho:id:credential",
    "commissionBps": 1000,
    "classes": ["engineering", "property"],
}


def register(book: str, profile: dict, actor: str):
    return A.one(REGISTER.format(book=book, profile=json.dumps(profile)),
                 key=actor, phlo_limit=2_000_000)


def main() -> int:
    if not preflight.require_devnet("broker"):
        print("not_run: devnet unavailable")
        return 2
    try:
        actors.ensure_vault("admin1")
        actors.ensure_vault("admin2")
        book = actors.resolve("component:broker-book")
        broker_owner = actors.address("admin1")

        A.cover('BrokerBook@"register"', "success")
        created = register(book, PROFILE, "admin1")
        A.expect_ok("register broker", created)
        broker_id, broker_uri = created[1], created[2]

        A.cover('BrokerBook@"brokerOf"', "success")
        A.expect("brokerOf", actors.invoke(book, "brokerOf", f'"{broker_owner}"'),
                 (True, broker_id, broker_uri))

        A.cover('BrokerBook@"brokers"', "success")
        brokers = actors.invoke(book, "brokers")
        A.expect_ok("brokers", brokers)
        A.expect("broker is indexed", broker_id in brokers[1], True)

        broker = broker_uri
        A.cover('Broker@"info"', "success")
        info = actors.invoke(broker, "info")
        A.expect_ok("broker info", info)
        A.expect("broker owner", info[1].get("ownerId"), broker_owner)

        A.cover('Broker@"profile"', "success")
        profile = actors.invoke(broker, "profile")
        A.expect_ok("broker profile", profile)
        A.expect("profile class list", profile[1].get("classes"),
                 ["engineering", "property"])

        A.cover('Broker@"slips"', "success")
        A.expect("no slips initially", actors.invoke(broker, "slips"), (True, {}))

        A.cover('Broker@"addSlip"', "success")
        added = A.one(ADD_SLIP.format(broker=broker, slip_id="slp:test"),
                      key="admin1", phlo_limit=2_000_000)
        A.expect_ok("addSlip", added)
        A.expect("slip indexed", actors.invoke(broker, "slips")[1].get("slp:test"),
                 "rho:id:test-slip")

        A.cover('BrokerBook@"register"', "refusal")
        A.expect_refusal("duplicate owner", register(book, PROFILE, "admin1"),
                         f"duplicate owner")
        bad_profile = dict(PROFILE, commissionBps=4000)
        A.expect_refusal("commission cap", register(book, bad_profile, "admin2"),
                         "commission")

        A.cover('BrokerBook@"brokerOf"', "refusal")
        A.expect_refusal("unknown broker",
                         actors.invoke(book, "brokerOf", '"unknown-owner"'),
                         "unknown broker")

        A.cover('Broker@"addSlip"', "refusal")
        # The deployer is not this broker's owner.
        A.expect_refusal("non-owner addSlip",
                         A.one(ADD_SLIP.format(broker=broker, slip_id="slp:other"),
                               phlo_limit=2_000_000),
                         "not owner")
    except Exception as error:
        print(f"broker suite failed: {error}", file=sys.stderr)
        A.finish("broker")
        return 1
    return A.finish("broker")


if __name__ == "__main__":
    raise SystemExit(main())
