#!/usr/bin/env python3
"""SyndicateBook/Syndicate: creation, capacity, quotes, members and lifecycle."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("syndicate"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.started("synd")
        book = p.component("component:syndicate-book")
        syn = p.syndicate_uri

        A.cover('SyndicateBook@"create"', "success")
        A.expect("syndicateOf", actors.invoke(book, "syndicateOf", f'"{p.owner_id}"'),
                 (True, p.syndicate_id, syn))
        A.cover('SyndicateBook@"syndicates"', "success")
        A.expect_ok("syndicates", actors.invoke(book, "syndicates"))
        A.cover('SyndicateBook@"byClass"', "success")
        A.expect("byClass", p.syndicate_id in actors.invoke(
            book, "byClass", '"property"')[1], True)
        A.cover('SyndicateBook@"count"', "success")
        A.expect("count", actors.invoke(book, "count")[1] >= 1, True)
        A.cover('SyndicateBook@"verify"', "success")
        verified = actors.invoke(book, "verify", f'"{syn}"')
        A.expect_ok("verify responds", verified)
        A.expect("verify returns a boolean", isinstance(verified[1], bool), True)

        A.cover('Syndicate@"info"', "success")
        info = p.syndicate_info()
        A.expect("syndicate owner", info.get("ownerId"), p.owner_id)
        A.cover('Syndicate@"capacity"', "success")
        cap = p.syndicate_capacity()
        A.expect("capacity capital at least the contribution", cap.get("capital") >= p.capital, True)
        current = p.syndicate_capacity()
        A.expect("capacity free", current.get("free"),
                 current["capital"] - current["committed"] - current["written"])
        A.cover('Syndicate@"members"', "success")
        members = actors.invoke(syn, "members")
        A.expect("owner is a member", p.owner_id in members[1], True)
        A.cover('Syndicate@"member"', "success")
        A.expect_ok("member", actors.invoke(syn, "member", f'"{p.owner_id}"'))

        A.cover('Syndicate@"quote"', "refusal")
        A.expect_refusal("unknown quote", actors.invoke(syn, "quote", '"q:missing"'),
                         "unknown quote")
        A.cover('Syndicate@"lines"', "success")
        lines = actors.invoke(syn, "lines")
        A.expect_ok("lines", lines)
        A.expect("lines is a map", isinstance(lines[1], dict), True)
        A.cover('Syndicate@"line"', "refusal")
        A.expect_refusal("unknown line", actors.invoke(syn, "line", '"lin:missing"'),
                         "unknown line")

        A.cover('Syndicate@"quote"', "success")
        p.subscribe()
        quote = p.quote_info()
        A.expect("quote records the slip", quote.get("slipId"), p.slip_id)
        A.expect("quote reserves capacity", quote.get("exposure") >= p.aggregate, True)

        A.cover('Syndicate@"setManager"', "success")
        A.expect_ok("setManager", actors.invoke(
            syn, "setManager", f'*dId, "{p.owner_id}"', key=p.insured))
        A.cover('Syndicate@"suspend"', "success")
        A.expect_ok("suspend", actors.invoke(syn, "suspend", "*dId", key=p.insured))
        A.expect("suspended", p.syndicate_info().get("status"), "suspended")
        A.cover('Syndicate@"resume"', "success")
        A.expect_ok("resume", actors.invoke(syn, "resume", "*dId", key=p.insured))
        A.expect("active", p.syndicate_info().get("status"), "active")

        A.cover('Syndicate@"withdrawCapital"', "refusal")
        withdrawal = actors.invoke(
            syn, "withdrawCapital", f"*dId, {cap['capital'] + 1}", key=p.insured)
        A.expect("withdraw above contribution refused",
                 withdrawal[0] is False and withdrawal[1] in {"amount", "capacity"}, True)
        A.cover('SyndicateBook@"syndicateOf"', "refusal")
        A.expect_refusal("unknown syndicate", actors.invoke(
            book, "syndicateOf", '"unknown-owner"'), "unknown syndicate")
    except Exception as error:
        print(f"syndicate suite failed: {error}", file=sys.stderr)
        A.finish("syndicate")
        return 1
    return A.finish("syndicate")


if __name__ == "__main__":
    raise SystemExit(main())
