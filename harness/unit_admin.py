#!/usr/bin/env python3
"""SureAdmin: 2-of-3 signatures, nonce replay and the global pause switch."""

import sys

import actors
import admin
import assertions as A
import preflight


def main() -> int:
    if not preflight.require_devnet("admin"):
        print("not_run: devnet unavailable")
        return 2
    try:
        uri = actors.resolve("component:admin")
        keys = actors.keys()

        A.cover('SureAdmin@"keys"', "success")
        configured = actors.invoke(uri, "keys")
        A.expect_ok("admin keys", configured)
        A.expect("three admins", len(configured[1]), 3)
        A.cover('SureAdmin@"nonce"', "success")
        nonce = actors.invoke(uri, "nonce")
        A.expect_ok("admin nonce", nonce)
        start = nonce[1]

        A.cover('SureAdmin@"admin"', "refusal")
        A.expect_refusal("empty signatures", actors.invoke(
            uri, "admin", f'{start + 1}, "pauseAll", [], []'), "below threshold")

        A.cover('SureAdmin@"admin"', "success")
        sigs = admin.admin_sigs(keys, "admin", start + 1, "pauseAll")
        A.expect_ok("pauseAll", actors.invoke(
            uri, "admin", f'{start + 1}, "pauseAll", [], {sigs}'))
        A.cover('SureAdmin@"isPaused"', "success")
        A.expect("paused", actors.invoke(uri, "isPaused"), (True, True))
        A.expect("nonce advanced", actors.invoke(uri, "nonce"), (True, start + 1))

        A.cover('SureAdmin@"admin"', "refusal")
        A.expect_refusal("nonce replay", actors.invoke(
            uri, "admin", f'{start + 1}, "resumeAll", [], {sigs}'), "replay")

        resume_sigs = admin.admin_sigs(keys, "admin", start + 2, "resumeAll")
        A.expect_ok("resumeAll", actors.invoke(
            uri, "admin", f'{start + 2}, "resumeAll", [], {resume_sigs}'))
        A.expect("resumed", actors.invoke(uri, "isPaused"), (True, False))
    except Exception as error:
        print(f"admin suite failed: {error}", file=sys.stderr)
        A.finish("admin")
        return 1
    return A.finish("admin")


if __name__ == "__main__":
    raise SystemExit(main())
