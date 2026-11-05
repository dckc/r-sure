#!/usr/bin/env python3
"""State-cell liveness: refusals and reads must not consume the cell."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("cell_liveness"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("liveness", syndicate_owner="deployer")
        line = p.line_uri(p.policy_lines()[0]["lineId"])

        A.cover('Policy@"info"', "success")
        before = p.policy_info()
        A.expect("policy read", isinstance(before, dict), True)
        A.expect_refusal("malformed claim does not consume policy", actors.invoke(
            p.policy_uri, "openClaim", "*dId, {}", key=p.insured), "fields")
        A.expect("policy still readable", p.policy_info().get("id"), before.get("id"))
        A.expect("policy nonce unchanged", p.policy_info().get("nonce"), before.get("nonce"))

        A.cover('Line@"info"', "success")
        line_before = p.line_info(line)
        A.expect_refusal("wrong line token does not consume line", actors.invoke(
            line, "pay", '*dId, "clm:x", 1, "owner"'), "not holder")
        line_after = p.line_info(line)
        A.expect("line still readable", line_after.get("lineId"), line_before.get("lineId"))
        A.expect("line state unchanged", line_after.get("paid"), line_before.get("paid"))

        A.cover('Slip@"info"', "success")
        slip_before = p.slip_info()
        A.expect_refusal("duplicate subscription does not consume slip", actors.invoke(
            p.slip_uri, "subscribe",
            f'*dId, "{p.syndicate_uri}", 100', key=p.insured), "closed")
        A.expect("slip still readable", p.slip_info().get("status"), slip_before.get("status"))

        A.cover('Syndicate@"info"', "success")
        A.expect("syndicate read", isinstance(p.syndicate_info(), dict), True)
        A.expect("syndicate read again", isinstance(p.syndicate_info(), dict), True)
    except Exception as error:
        print(f"cell_liveness suite failed: {error}", file=sys.stderr)
        A.finish("cell_liveness")
        return 1
    return A.finish("cell_liveness")


if __name__ == "__main__":
    raise SystemExit(main())
