#!/usr/bin/env python3
"""Kernel behaviour: Clock monotonicity, Verifier determinism, Codec shape."""

import sys

import actors
import assertions as A
import preflight


def main() -> int:
    if not preflight.require_devnet("behavior"):
        print("not_run: devnet unavailable")
        return 2
    try:
        clock = actors.resolve("component:clock")
        verifier = actors.resolve("component:verifier")
        codec = actors.resolve("component:codec")

        A.cover('Clock@"now"', "success")
        first = actors.invoke(clock, "now")
        A.expect_ok("clock now", first)
        A.expect("clock returns a height", isinstance(first[1], int), True)
        second = actors.invoke(clock, "now")
        A.expect("clock is monotone", second[1] >= first[1], True)

        A.cover('Verifier@"hash"', "success")
        one = actors.invoke(verifier, "hash", '"abc".toUtf8Bytes()')
        same = actors.invoke(verifier, "hash", '"abc".toUtf8Bytes()')
        other = actors.invoke(verifier, "hash", '"abd".toUtf8Bytes()')
        A.expect_ok("verifier hash", one)
        A.expect("verifier hash deterministic", one, same)
        A.expect("verifier hash separates inputs", one != other, True)

        A.cover('Verifier@"sigOk"', "refusal")
        bad = actors.invoke(verifier, "sigOk",
                            '"00".hexToBytes(), "00".hexToBytes(), "00".hexToBytes()')
        A.expect_ok("verifier sigOk responds", bad)
        A.expect("verifier refuses a malformed signature", bad[1], False)

        A.cover('Codec@"canonical"', "success")
        canonical = actors.invoke(codec, "canonical", '"sch", ["a", "b"]')
        A.expect_ok("canonical", canonical)
        A.expect("canonical joins with a separator", canonical[1], "sch|a|b")

        A.cover('Codec@"hash"', "success")
        hashed = actors.invoke(codec, "hash", '"sch", ["a", "b"]')
        A.expect_ok("codec hash", hashed)

        A.cover('Codec@"adminPayload"', "success")
        payload = actors.invoke(codec, "adminPayload",
                                '"root", 1, "freeze", []')
        A.expect("adminPayload is domain separated",
                 str(payload).startswith("rsure:admin:v1|root|1|freeze|"), True)
    except Exception as error:
        print(f"behavior suite failed: {error}", file=sys.stderr)
        A.finish("behavior")
        return 1
    return A.finish("behavior")


if __name__ == "__main__":
    raise SystemExit(main())
