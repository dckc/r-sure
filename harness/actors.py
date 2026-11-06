#!/usr/bin/env python3
"""Actors, REV accounts, payments and insurance-payout helpers.

The devnet bakes in one funded deployer. Every other key needs a faucet drip before it can
sign a deploy; r-cash's keygen funds them during setup, and this module repairs a stale key
set by dripping on demand.  ``pay`` moves REV from an actor's r-cash account into a
contract arm (premiums and capital); ``balance`` reads the account the contracts pay out
to.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

# RSURE_* is the canonical prefix.  Bridge it onto the RSHARE_* names read by
# `deploy.py` before that module is imported, so older CI environments keep working.
_ENV_NAMES = ("NODE", "ADMIN", "CONTAINER", "SHARD", "PHLO_LIMIT", "PHLO_PRICE", "KEYS")
for _name in _ENV_NAMES:
    _value = os.environ.get(f"RSURE_{_name}")
    if _value is not None:
        os.environ[f"RSHARE_{_name}"] = _value


def env(name: str, default: str | None = None) -> str | None:
    """Read ``RSURE_<name>``, falling back to the legacy ``RSHARE_<name>``."""
    value = os.environ.get(f"RSURE_{name}")
    if value is not None:
        return value
    return os.environ.get(f"RSHARE_{name}", default)


from assertions import one, root_call, root_uri  # noqa: E402

import deploy as node  # noqa: E402

PING = 'new deployId(`rho:rchain:deployId`) in { deployId!(1) }'

def _nonce_reply(reply, label: str) -> int:
    if (
        isinstance(reply, tuple)
        and len(reply) >= 2
        and reply[0] is True
        and isinstance(reply[1], int)
        and reply[1] >= 0
    ):
        return reply[1]
    raise AssertionError(f"{label} nonce: {reply!r}")


def admin_nonce_read() -> int:
    """The current global admin nonce, read from ShareAdmin("nonce")."""
    admin = resolve("component:admin")
    return _nonce_reply(invoke(admin, "nonce"), "admin")


def root_nonce_read() -> int:
    """The current governance nonce, read from ShareRoot("nonce")."""
    return _nonce_reply(one(root_call("nonce")), "root")


def keys() -> dict:
    return node.load_keys()


def public(name: str = "deployer") -> str:
    return keys()[name]["public"]


def address(name: str = "deployer") -> str:
    return keys()[name]["address"]


def call_term(uri: str, binding: str, args: str | None = None) -> str:
    head = json.dumps(binding)
    if args is not None:
        head += f", {args}"
    return f"""
new rl(`rho:registry:lookup`), ch, ret,
    dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{uri}`, *ch) |
  for (C <- ch) {{
    C!({head}, *ret) |
    for (@r <- ret) {{ deployId!(r) }}
  }}
}}
"""


def invoke(uri: str, binding: str, args: str | None = None, key: str = "deployer",
           phlo_limit: int = 10_000_000):
    return one(call_term(uri, binding, args), key=key, phlo_limit=phlo_limit)


def resolve(component: str, key: str = "deployer"):
    reply = invoke(root_uri(), "resolve", f'"{component}", 1', key=key)
    if not (isinstance(reply, tuple) and reply[0] is True):
        raise AssertionError(f"resolve {component}: {reply!r}")
    return reply[1]


def _ping(name: str, min_phlo: int) -> tuple[bool, object]:
    """Return ``(precharged, detail)`` for a deploy that emits ``1``.

    A precharge failure is reported by some node versions as a deploy result tuple
    rather than a ``DevnetError``.  Treat anything other than the literal ``1`` as a
    failure so the caller drips the faucet instead of trusting a false reply.
    """
    try:
        reply = one(PING, key=name, phlo_limit=min_phlo)
    except node.DevnetError as error:
        if "insufficient funds" not in str(error):
            raise
        return False, error
    return reply == 1, reply


def ensure_vault(name: str, min_phlo: int = 10_000_000) -> None:
    """Prove the key can precharge a race-sized deploy; drip the faucet if it cannot."""
    ready, detail = _ping(name, min_phlo)
    if ready:
        return

    last: object = detail
    for _ in range(6):
        try:
            node.faucet(address(name))
        except Exception as error:  # rate limited or already queued
            last = error
        time.sleep(2)
        ready, detail = _ping(name, min_phlo)
        if ready:
            return
        last = detail
    raise AssertionError(f"actor {name} has no phlo: {last!r}")


def block_height() -> int:
    term = """
new bd(`rho:block:data`), ch, deployId(`rho:rchain:deployId`) in {
  bd!(*ch) |
  for (@n, @sender, @timestamp <- ch) { deployId!(n) }
}
"""
    height = one(term)
    if not isinstance(height, int):
        raise AssertionError(f"block height: {height!r}")
    return height


def wait_height(target: int, timeout: float = 180.0) -> int:
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = node.height()
        if current >= target:
            return current
        one(PING, phlo_limit=1_000_000)
    raise AssertionError(f"height {target} not reached in {timeout}s")


def ensure_account(name: str) -> str:
    term = f"""
new rl(`rho:registry:lookup`), rootCh, afCh, ac, oCh,
    deployId(`rho:rchain:deployId`) in {{
  rl!(`{rcash_root_uri()}`, *rootCh) |
  for (Root <- rootCh) {{
    Root!("resolve", "component:account-factory", 1, *afCh) |
    for (@(true, afUri, _) <- afCh) {{
      rl!(afUri, *ac) |
      for (AccountFactory <- ac) {{
        AccountFactory!("getOrCreate", "{public(name)}".hexToBytes(), *oCh) |
        for (@(true, account, ownerId) <- oCh) {{ deployId!(ownerId) }}
      }}
    }}
  }}
}}
"""
    owner = one(term, key=name, phlo_limit=2_000_000)
    if not isinstance(owner, str):
        raise AssertionError(f"account for {name}: {owner!r}")
    return owner


def fund(name: str, amount: int = 2_000) -> int:
    """Mint REV into an actor's r-cash account and return the new balance."""
    if amount < 1 or amount > 100_000:
        raise ValueError("funding amount must be 1..100000")
    term = f"""
new rl(`rho:registry:lookup`), rootCh, afCh, ac, oCh, fCh, bCh,
    ertpCh, revIssuerCh, purseCh, fundCh, wdCh, depCh,
    deployId(`rho:rchain:deployId`), deployerId(`rho:rchain:deployerId`) in {{
  rl!(`{rcash_root_uri()}`, *rootCh) |
  rl!(`rho:rchain:ertp`, *ertpCh) |
  for (Root <- rootCh; @(_, ERTP) <- ertpCh) {{
    Root!("resolve", "component:account-factory", 1, *afCh) |
    for (@(true, afUri, _) <- afCh) {{
      rl!(afUri, *ac) |
      for (AccountFactory <- ac) {{
        AccountFactory!("getOrCreate", "{public(name)}".hexToBytes(), *oCh) |
        for (@(true, account, ownerId) <- oCh) {{
          @account!("depositFacet", "REV", *fCh) |
          for (@fr <- fCh) {{
            match fr {{
              (true, facet) => {{
                @ERTP!("getRevIssuer", *revIssuerCh) |
                for (@(revBrand, revIssuer) <- revIssuerCh) {{
                  @revIssuer!("makeEmptyPurse", *purseCh) |
                  for (@(true, purse) <- purseCh) {{
                    @purse!("revFund", *deployerId, 100000, *fundCh) |
                    for (@_ <- fundCh) {{
                      @purse!("withdraw", (revBrand, {amount}), *wdCh) |
                      for (@(true, payment) <- wdCh) {{
                        @facet!("deposit", payment, *depCh) |
                        for (@d <- depCh) {{
                          match d {{
                            (true, balance) => {{ deployId!([ownerId, balance]) }}
                            _ => {{ deployId!(d) }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
              _ => {{ deployId!(fr) }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""
    reply = one(term, key=name, phlo_limit=2_000_000)
    if not (isinstance(reply, list) and len(reply) == 2 and isinstance(reply[1], int)):
        raise AssertionError(f"fund {name}: {reply!r}")
    return reply[1]


def balance(name: str = "deployer") -> int:
    term = f"""
new rl(`rho:registry:lookup`), rootCh, afCh, ac, oCh, bCh,
    deployId(`rho:rchain:deployId`), deployerId(`rho:rchain:deployerId`) in {{
  rl!(`{rcash_root_uri()}`, *rootCh) |
  for (Root <- rootCh) {{
    Root!("resolve", "component:account-factory", 1, *afCh) |
    for (@(true, afUri, _) <- afCh) {{
      rl!(afUri, *ac) |
      for (AccountFactory <- ac) {{
        AccountFactory!("getOrCreate", "{public(name)}".hexToBytes(), *oCh) |
        for (@(true, account, ownerId) <- oCh) {{
          @account!("balance", *deployerId, "REV", *bCh) |
          for (@b <- bCh) {{ deployId!(b) }}
        }}
      }}
    }}
  }}
}}
"""
    reply = one(term, key=name, phlo_limit=2_000_000)
    if not (isinstance(reply, tuple) and reply[0] is True and isinstance(reply[1], int)):
        raise AssertionError(f"balance {name}: {reply!r}")
    return reply[1]


def ensure_funds(name: str, amount: int, chunk: int = 100_000) -> int:
    """Ensure an actor's r-cash account holds at least ``amount`` REV."""
    if amount < 0:
        raise ValueError("amount must be non-negative")
    balance_now = balance(name)
    while balance_now < amount:
        balance_now = fund(name, min(amount - balance_now, chunk))
    return balance_now


def payment_term(uri: str, binding: str, args: list[str], amount: int,
                 key: str = "deployer", asset_id: str = "REV") -> str:
    """Withdraw ``amount`` from ``key``'s r-cash account and call a contract with it.

    ``args`` is a list of Rholang expressions.  The token ``"$payment"`` is replaced by
    the locally bound ``payment`` name; every other entry is emitted verbatim.  This is
    how a premium payment reaches ``Slip("fundPremium")`` and a capital contribution
    reaches ``Syndicate("contribute")`` without exposing the payment as a deploy result.
    """
    if amount < 1:
        raise ValueError("payment amount must be positive")
    rendered = ", ".join(
        "payment" if item == "$payment" else item for item in args)
    head = json.dumps(binding)
    if rendered:
        head += f", {rendered}"
    return f"""
new rl(`rho:registry:lookup`), rootCh, afCh, ac, oCh, wdCh, cCh, ret,
    dId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{rcash_root_uri()}`, *rootCh) |
  for (Root <- rootCh) {{
    Root!("resolve", "component:account-factory", 1, *afCh) |
    for (@(true, afUri, _) <- afCh) {{
      rl!(afUri, *ac) |
      for (AccountFactory <- ac) {{
        AccountFactory!("getOrCreate", "{public(key)}".hexToBytes(), *oCh) |
        for (@(true, account, _) <- oCh) {{
          @account!("withdraw", *dId, "{asset_id}", {int(amount)}, *wdCh) |
          for (@w <- wdCh) {{
            match w {{
              (true, payment) => {{
                rl!(`{uri}`, *cCh) |
                for (C <- cCh) {{
                  C!({head}, *ret) |
                  for (@r <- ret) {{ deployId!(r) }}
                }}
              }}
              _ => {{ deployId!(w) }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""


def pay(uri: str, binding: str, args: list[str], amount: int,
        key: str = "deployer", asset_id: str = "REV", phlo_limit: int = 5_000_000):
    """Pay a contract arm from an actor's REV account and return its reply."""
    return one(
        payment_term(uri, binding, args, amount, key=key, asset_id=asset_id),
        key=key, phlo_limit=phlo_limit)


def pay_premium(slip_uri: str, amount: int, key: str = "business"):
    """Fund a slip's premium purse from the insured's REV account."""
    return pay(slip_uri, "fundPremium", ["*dId", "$payment"], amount, key=key)


def contribute_syndicate(syndicate_uri: str, amount: int, key: str = "business"):
    """Contribute underwriting capital from the syndicate owner's REV account."""
    return pay(syndicate_uri, "contribute", ["*dId", "$payment"], amount, key=key)


def contribute_fund(fund_uri: str, amount: int, policy_id: str,
                    key: str = "business"):
    """Pay a central-fund contribution for one policy."""
    return pay(fund_uri, "contribute", ["$payment", json.dumps(policy_id)],
               amount, key=key)


def rcash_root_uri() -> str:
    from rcash_paths import configured_manifest

    cfg = json.loads((Path(__file__).resolve().parent.parent
                      / "configs" / "devnet.json").read_text())
    manifest = configured_manifest(cfg["rcash_manifest"])
    return json.loads(manifest.read_text())["root_uri"]
