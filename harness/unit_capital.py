#!/usr/bin/env python3
"""Syndicate capital: contribution, capacity and withdrawal bounds."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("capital"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.started("capital", syndicate_owner="deployer", capital=7000)
        syn = p.syndicate_uri
        before = p.syndicate_capacity()

        A.cover('Syndicate@"contribute"', "success")
        A.expect_ok("contribute capital", actors.contribute_syndicate(syn, 25, key=p.insured))
        after = p.syndicate_capacity()
        A.expect("contribution increases capital", after["capital"], before["capital"] + 25)

        A.cover('Syndicate@"members"', "success")
        member = actors.invoke(syn, "member", f'"{p.owner_id}"')
        A.expect_ok("member record", member)
        A.expect("contributed at least the capital", member[1].get("contributed") >= 25, True)

        A.cover('Syndicate@"withdrawCapital"', "success")
        A.expect_ok("withdraw one unit",
                    actors.invoke(syn, "withdrawCapital", "*dId, 1", key=p.insured))
        withdrawn = p.syndicate_capacity()
        A.expect("withdrawal decreases capital", withdrawn["capital"], after["capital"] - 1)

        A.cover('Syndicate@"withdrawCapital"', "refusal")
        refusal = actors.invoke(syn, "withdrawCapital",
                                f"*dId, {withdrawn['capital'] + 1}", key=p.insured)
        A.expect("over-withdrawal refused",
                 refusal[0] is False and refusal[1] in {"amount", "capacity"}, True)

        A.cover('Syndicate@"capacity"', "success")
        cap = p.syndicate_capacity()
        A.expect("free capacity non-negative", cap["free"] >= 0, True)
        A.expect("free is capital minus commitments",
                 cap["free"], cap["capital"] - cap["committed"] - cap["written"])
    except Exception as error:
        print(f"capital suite failed: {error}", file=sys.stderr)
        A.finish("capital")
        return 1
    return A.finish("capital")


if __name__ == "__main__":
    raise SystemExit(main())
