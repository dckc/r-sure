#!/usr/bin/env python3
"""2-of-3 admin signatures over the canonical on-chain payload.

Every admin action is signed over the payload produced by the deployed
``Codec("adminPayload", ...)`` arm:

    rsure:admin:v1|<domain>|<nonce>|<action>|<arg0>,<arg1>,...

The digest is ``blake2b256(utf8(payload))`` and the signatures are DER-encoded
secp256k1 over that digest.  Python never rebuilds the payload; it asks the chain so
the off-chain signer and the on-chain guard cannot drift apart.

Domains used by the deployment: ``root`` (SureRoot governance), ``admin``
(SureAdmin), ``payments`` (Payments), and ``fund`` (SureFund).  Instance contracts
that keep their own admin set use their own domain, for example ``booking:<id>``.
"""

from __future__ import annotations

import hashlib
import json

import actors

ADMIN_NAMES = ("admin1", "admin2", "admin3")
SIGNERS = ("admin1", "admin2")


def rholang_string(text: str) -> str:
    """Return a quoted Rholang string literal (JSON escaping is compatible here)."""
    return json.dumps(text)


def admin_names(keys: dict | None = None) -> list[str]:
    """The admin keys present in the key set, in canonical order."""
    keys = actors.keys() if keys is None else keys
    return [name for name in ADMIN_NAMES if name in keys]


def admin_literal(keys: dict, names: list[str] | None = None) -> str:
    """A Rholang list literal of compressed public keys, ready to pass on chain."""
    names = list(names or ADMIN_NAMES)
    missing = [name for name in names if name not in keys]
    if missing:
        raise KeyError(f"admin keys missing from the key set: {missing}")
    return "[" + ", ".join(
        f'"{keys[name]["public"]}".hexToBytes()' for name in names) + "]"


def codec_uri() -> str:
    """Resolve the deployed canonical codec."""
    return actors.resolve("component:codec")


def payload(codec: str, domain: str, nonce: int, action: str,
            args_literal: str) -> str:
    """Ask the on-chain codec for the canonical admin payload."""
    reply = actors.invoke(
        codec, "adminPayload",
        f"{rholang_string(domain)}, {int(nonce)}, {rholang_string(action)}, "
        f"{args_literal}")
    if not isinstance(reply, str):
        raise AssertionError(f"adminPayload {domain}/{action}: {reply!r}")
    return reply


def payload_for(domain: str, nonce: int, action: str, args_literal: str,
                codec: str | None = None) -> str:
    """Canonical payload using the deployed codec unless one is supplied."""
    return payload(codec or codec_uri(), domain, nonce, action, args_literal)


def digest(payload_text: str) -> bytes:
    """The digest the chain hashes before secp256k1 verification."""
    return hashlib.blake2b(payload_text.encode(), digest_size=32).digest()


def signature(keys: dict, name: str, payload_text: str) -> str:
    """One DER signature as a Rholang byte-array literal."""
    from coincurve import PrivateKey

    if name not in keys:
        raise KeyError(f"signer {name!r} is not in the key set")
    key = PrivateKey(bytes.fromhex(keys[name]["secret"]))
    signed = key.sign(digest(payload_text), hasher=None)
    return f'"{signed.hex()}".hexToBytes()'


def sign(keys: dict, names: list[str] | tuple[str, ...], payload_text: str) -> str:
    """A Rholang list literal holding one signature per named key."""
    return "[" + ", ".join(
        signature(keys, name, payload_text) for name in names) + "]"


def args_literal(args_text: str = "") -> str:
    """Encode comma-joined canonical text as the single-element codec argument list.

    ``Codec("adminPayload", ...)`` joins the list arguments with commas.  Passing one
    string (``["k,1,uri,2"]``) therefore produces exactly ``k,1,uri,2`` without needing
    the pinned node to ``toString`` a list.
    """
    if args_text == "":
        return "[]"
    return f"[{rholang_string(args_text)}]"


def signed(keys: dict, domain: str, nonce: int, action: str,
           args_text: str = "", names: list[str] | tuple[str, ...] | None = None,
           codec: str | None = None,
           args: str | None = None) -> tuple[str, str]:
    """Return ``(signatures_literal, payload_text)`` for one admin action.

    ``args`` overrides ``args_text`` when the action needs a real argument list (for
    example ``["<admins-text>", 2]`` for ``setAdmins``); ``args_text`` is then unused.
    """
    literal = args if args is not None else args_literal(args_text)
    text = payload_for(domain, nonce, action, literal, codec=codec)
    return sign(keys, names or SIGNERS, text), text


def admin_sigs(keys: dict, domain: str, nonce: int, action: str,
               args_text: str = "", names: list[str] | tuple[str, ...] | None = None,
               codec: str | None = None, args: str | None = None) -> str:
    """Signatures for an admin action, with the payload fetched from the chain."""
    return signed(keys, domain, nonce, action, args_text=args_text, names=names,
                  codec=codec, args=args)[0]


def rotate_args_text(key: str, expected_version: int, new_uri: str,
                     new_version: int) -> str:
    """Canonical text for ``SureRoot("rotate", ...)``."""
    return f"{key},{int(expected_version)},{new_uri},{int(new_version)}"


def set_admins_args(keys: dict, names: list[str] | None = None,
                    threshold: int = 2) -> tuple[str, str]:
    """Return ``(call_literal, payload_args)`` for a ``setAdmins`` action.

    The call literal is the list of admin public keys; the payload argument list carries
    the canonical comma-joined hex text plus the threshold.
    """
    names = list(names or ADMIN_NAMES)
    literal = admin_literal(keys, names)
    text = ",".join(keys[name]["public"] for name in names)
    return literal, f"[{rholang_string(text)}, {int(threshold)}]"
