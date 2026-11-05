#!/usr/bin/env python3
"""SureRoot: resolve, keys, nonce, installer authority and refusal paths."""

import sys

import actors
import assertions as A
import preflight


REGISTER_TERM = """
new rl(`rho:registry:lookup`), ch, ret,
    dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{root}`, *ch) |
  for (SureRoot <- ch) {{
    SureRoot!("register", "{key}", "rho:id:probe", {version}, "probe", *dId, *ret) |
    for (@r <- ret) {{ deployId!(r) }}
  }}
}}
"""


def register(key: str, version: int = 1, actor: str = "deployer"):
    return A.one(REGISTER_TERM.format(root=A.root_uri(), key=key, version=version),
                 key=actor, phlo_limit=2_000_000)


def main() -> int:
    if not preflight.require_devnet("root"):
        print("not_run: devnet unavailable")
        return 2
    try:
        actors.ensure_vault("admin1")

        A.cover('SureRoot@"resolve"', "success")
        A.expect_ok("resolve clock", A.one(A.root_call("resolve", '"component:clock", 1')))
        A.cover('SureRoot@"resolve"', "refusal")
        A.expect_refusal("resolve unknown",
                         A.one(A.root_call("resolve", '"component:missing", 1')),
                         "unknown component")

        A.cover('SureRoot@"keys"', "success")
        keys = A.one(A.root_call("keys"))
        A.expect_ok("keys", keys)
        A.expect("keys include clock", "component:clock" in keys[1], True)

        A.cover('SureRoot@"nonce"', "success")
        A.expect("nonce starts at zero", A.one(A.root_call("nonce")), (True, 0))

        A.cover('SureRoot@"resolveMany"', "success")
        many = A.one(A.root_call("resolveMany",
                                 '["component:clock", "component:admin"], 1'))
        A.expect_ok("resolveMany", many)
        A.expect("resolveMany has both keys", sorted(many[1].keys()),
                 ["component:admin", "component:clock"])

        A.cover('SureRoot@"register"', "refusal")
        A.expect_refusal("non-installer register", register("probe:unauthorised", actor="admin1"),
                         "not installer")
        A.expect_refusal("duplicate register", register("component:clock"), "duplicate")

        A.cover('SureRoot@"freeze"', "refusal")
        A.expect_refusal("freeze below threshold",
                         A.one(A.root_call("freeze", "100, []")), "below threshold")

        A.cover('SureRoot@"rotate"', "refusal")
        A.expect_refusal("rotate below threshold",
                         A.one(A.root_call(
                             "rotate",
                             '"component:clock", 1, "rho:id:probe", 2, 100, []')),
                         "below threshold")
    except Exception as error:
        print(f"root suite failed: {error}", file=sys.stderr)
        A.finish("root")
        return 1
    return A.finish("root")


if __name__ == "__main__":
    raise SystemExit(main())
