#!/usr/bin/env python3
"""AdminGuard and Codec: canonical payload, 2-of-3 distinct keys and domain separation."""

import sys

import actors
import admin
import assertions as A
import preflight


def main() -> int:
    if not preflight.require_devnet("admin_keys"):
        print("not_run: devnet unavailable")
        return 2
    try:
        guard = actors.resolve("component:admin-guard")
        keys = actors.keys()
        admins = admin.admin_literal(keys)
        sigs = admin.admin_sigs(keys, "admin", 7, "pauseAll", names=("admin1", "admin2"))
        one = admin.admin_sigs(keys, "admin", 7, "pauseAll", names=("admin1",))

        A.cover('AdminGuard@"verify"', "success")
        A.expect("two distinct signatures accepted", actors.invoke(
            guard, "verify",
            f'"admin", 7, "pauseAll", [], {sigs}, {admins}, 2'), (True, True))
        A.cover('AdminGuard@"verify"', "refusal")
        A.expect_refusal("one signature is below threshold", actors.invoke(
            guard, "verify",
            f'"admin", 7, "pauseAll", [], {one}, {admins}, 2'), "below threshold")
        A.expect_refusal("wrong domain rejected", actors.invoke(
            guard, "verify",
            f'"root", 7, "pauseAll", [], {sigs}, {admins}, 2'), "below threshold")

        codec = actors.resolve("component:codec")
        A.cover('Codec@"adminPayload"', "success")
        payload = admin.payload_for("admin", 7, "pauseAll", "[]", codec=codec)
        A.expect("payload domain", payload.startswith("rsure:admin:v1|admin|7|pauseAll|"), True)
        A.expect("payload is deterministic", admin.payload_for(
            "admin", 7, "pauseAll", "[]", codec=codec), payload)
        A.expect("domain separation changes the payload",
                 admin.payload_for("root", 7, "pauseAll", "[]", codec=codec) != payload, True)
    except Exception as error:
        print(f"admin_keys suite failed: {error}", file=sys.stderr)
        A.finish("admin_keys")
        return 1
    return A.finish("admin_keys")


if __name__ == "__main__":
    raise SystemExit(main())
