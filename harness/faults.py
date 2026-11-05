#!/usr/bin/env python3
"""Test-only component fault injection through the deployed Root.

The helpers rotate a component key to a refusing stub URI and restore the original in
the caller's ``finally``.  They never edit contract source and never touch a production
manifest.  Refusing stubs let a suite prove that a caller handles a dependency outage
without moving value; factory stubs prove the same for creation paths.
"""

from __future__ import annotations

import admin
import actors
from assertions import one, root_uri


def deploy_stub(term: str) -> str:
    uri = one(term)
    if not isinstance(uri, str) or not uri.startswith("rho:id:"):
        raise AssertionError(f"stub URI: {uri!r}")
    return uri


def refusing_term(name: str, arms: dict[str, tuple[str, ...]],
                  reason: str = "unavailable") -> str:
    """The Rholang term for a contract whose named arms all refuse with ``reason``.

    ``arms`` maps an arm label to the argument patterns *before* the reply channel,
    e.g. ``{"open": ("dId", "@req")}``.  The reply channel is appended automatically.
    """
    clauses = []
    for arm, patterns in arms.items():
        params = ", ".join(patterns)
        head = f"@{arm}" if not patterns else f'@"{arm}", {params}'
        clauses.append(
            f"  contract {name}({head}, ret) = {{ ret!((false, \"{reason}\")) }}")
    body = " |\n".join(clauses)
    return f"""
new {name}, rs(`rho:registry:insertArbitrary`), ch,
    deployId(`rho:rchain:deployId`) in {{
{body} |
  rs!(bundle+{{*{name}}}, *ch) |
  for (@uri <- ch) {{ deployId!(uri) }}
}}
"""


def refusing_contract(name: str, arms: dict[str, tuple[str, ...]],
                      reason: str = "unavailable") -> str:
    """Deploy one refusing contract stub and return its URI."""
    return deploy_stub(refusing_term(name, arms, reason))


# ---- dependency stubs ----------------------------------------------------------------


def fake_payments() -> str:
    """A Payments component that refuses every arm."""
    return refusing_contract("Payments", {
        "health": (),
        "ensureAccount": ("dId",),
        "accountOf": ("@ownerId",),
        "depositFacet": ("@ownerId", "@assetId"),
        "issuer": ("@assetId",),
        "platformOwner": (),
        "admin": ("@nonce", "@action", "@args", "@sigs"),
    })


def fake_rgen() -> str:
    """An RgenAdapter component that refuses every arm."""
    return refusing_contract("RgenAdapter", {
        "health": (),
        "config": (),
        "oracleFactory": (),
        "credentialFactory": (),
        "claimFactory": (),
        "verifyCredential": ("@uri",),
        "verifyClaim": ("@uri",),
        "verifyProvenance": ("@uri", "@hash"),
        "admin": ("@nonce", "@action", "@args", "@sigs"),
    })


# ---- factory stubs -------------------------------------------------------------------


def fake_slip_factory() -> str:
    return refusing_contract("SlipFactory", {"open": ("dId", "@req")})


def fake_policy_factory() -> str:
    return refusing_contract("PolicyFactory", {
        "create": ("@req", "purse", "brand", "policyToken", "claimToken")})


def fake_claim_factory() -> str:
    return refusing_contract("ClaimFactory", {
        "create": ("dId", "@policyUri", "@policyId", "@insured", "@broker",
                   "claimToken", "@req")})


def fake_line_factory() -> str:
    return refusing_contract("LineFactory", {
        "create": ("@req", "creditCap", "settleCap", "releaseCap", "policyToken")})


def fake_distribution_factory() -> str:
    return refusing_contract("DistributionFactory", {
        "create": ("@purse", "@brand", "@assetId", "@policyId", "@base", "@plan",
                   "policyToken")})


def fake_risk_book() -> str:
    return refusing_contract("RiskBook", {
        "submit": ("dId", "@req"), "risk": ("@riskId",), "risks": (),
        "byInsured": ("@insured",), "byBroker": ("@broker",)})


def fake_broker_book() -> str:
    return refusing_contract("BrokerBook", {
        "register": ("dId", "@profile"), "brokerOf": ("@ownerId",),
        "brokers": ()})


def fake_syndicate_book() -> str:
    return refusing_contract("SyndicateBook", {
        "create": ("dId", "@profile"), "syndicateOf": ("@ownerId",),
        "syndicates": (), "byClass": ("@class",), "count": (), "verify": ("@uri",)})


# ---- root rotation -------------------------------------------------------------------


def rotate_component(key: str, new_uri: str, new_version: int = 1):
    """Point ``key`` at ``new_uri``.  Return the original ``(uri, version)``."""
    root = root_uri()
    current = actors.invoke(root, "resolve", f'"{key}", 1')
    if not (isinstance(current, tuple) and current[0] is True):
        raise AssertionError(f"resolve {key}: {current!r}")
    original_uri, original_version = current[1], current[2]
    nonce = actors.root_nonce_read() + 1
    args_text = admin.rotate_args_text(key, original_version, new_uri, new_version)
    sigs = admin.admin_sigs(actors.keys(), "root", nonce, "rotate", args_text)
    reply = actors.invoke(
        root, "rotate",
        f'"{key}", {original_version}, "{new_uri}", {new_version}, {nonce}, {sigs}')
    if not (isinstance(reply, tuple) and reply[0] is True):
        raise AssertionError(f"rotate {key}: {reply!r}")
    return original_uri, original_version


def restore_component(key: str, original_uri: str, original_version: int) -> None:
    """Restore ``key`` to its pre-rotation URI and version."""
    root = root_uri()
    current = actors.invoke(root, "resolve", f'"{key}", 1')
    if not (isinstance(current, tuple) and current[0] is True):
        raise AssertionError(f"resolve {key}: {current!r}")
    current_version = current[2]
    nonce = actors.root_nonce_read() + 1
    args_text = admin.rotate_args_text(
        key, current_version, original_uri, original_version)
    sigs = admin.admin_sigs(actors.keys(), "root", nonce, "rotate", args_text)
    reply = actors.invoke(
        root, "rotate",
        f'"{key}", {current_version}, "{original_uri}", {original_version}, '
        f'{nonce}, {sigs}')
    if not (isinstance(reply, tuple) and reply[0] is True):
        raise AssertionError(f"restore {key}: {reply!r}")
