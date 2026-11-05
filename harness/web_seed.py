#!/usr/bin/env python3
"""Seed demo placements for the r-sure web client.

Every catalogue URI is produced by a real deploy on a running devnet.  The script makes
two placements:

* ``web-open``  — syndicate, broker, risk and an open slip, for discovery;
* ``web-bound`` — the same through bind, plus one settled claim and one claim left open
  so the claims pages have live states to show.

It then writes ``deployments/catalogue.json``.  The app fetches that file from
``public/``; run ``npm run build`` (or ``make web-build``) to serve the new catalogue.

The web app's wallet is created in the browser, so this script does not export demo
keystores: the catalogue is a discovery aid, not a login.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))

import actors  # noqa: E402
import assertions  # noqa: E402
import deploy as node  # noqa: E402
import placement_fixture as fixture  # noqa: E402
import preflight  # noqa: E402


def entry(kind: str, uri: str, label: str, *,
          class_: str | None = None, insured: str | None = None,
          broker: str | None = None) -> dict:
    value = {"kind": kind, "uri": uri, "label": label}
    if class_ is not None:
        value["class"] = class_
    if insured is not None:
        value["insured"] = insured
    if broker is not None:
        value["broker"] = broker
    return value


def placement_entries(placement: fixture.Placement) -> list[dict]:
    insured = actors.address(placement.insured)
    entries = [
        entry("syndicates", placement.syndicate_uri,
              f"Syndicate · {placement.name}", class_=placement.class_),
        entry("brokers", placement.broker_uri,
              f"Broker · {placement.name}", insured=insured),
        entry("risks", placement.risk_uri,
              f"Risk · {placement.name}", class_=placement.class_,
              insured=insured, broker=placement.broker_uri),
        entry("slips", placement.slip_uri,
              f"Slip · {placement.name}", class_=placement.class_,
              insured=insured, broker=placement.broker_uri),
    ]
    if placement.policy_uri:
        entries.append(
            entry("policies", placement.policy_uri,
                  f"Policy · {placement.name}", class_=placement.class_,
                  insured=insured, broker=placement.broker_uri)
        )
    if placement.claim_uri:
        entries.append(
            entry("claims", placement.claim_uri,
                  f"Claim · {placement.name}", class_=placement.class_,
                  insured=insured)
        )
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path,
                        default=ROOT / "deployments" / "catalogue.json")
    parser.add_argument("--seed", type=Path, default=ROOT / ".demo" / "seed-devnet.json")
    args = parser.parse_args(argv)

    if not preflight.require_devnet("web_seed"):
        return 2

    status = node.http_json("GET", f"{node.NODE}/api/v1/status")
    manifest = json.loads(assertions.MANIFEST.read_text())

    print("web_seed: open placement")
    open_placement = fixture.started(
        "web-open", insured="business", class_="engineering")
    print(f"  slip {open_placement.slip_uri}")

    print("web_seed: bound placement")
    bound = fixture.bound("web-bound", insured="sender", class_="property")
    print(f"  policy {bound.policy_uri}")

    print("web_seed: settled claim")
    settled = bound.claim(amount=bound.per_claim)
    print(f"  claim {settled}")

    print("web_seed: open claim")
    live = fixture.started("web-claim", insured="recipient", class_="marine")
    policy = live.bind_all()
    live.open_claim(amount=live.per_claim // 2)
    live.classify_claim()
    live.assess_claim()
    print(f"  policy {policy}")
    print(f"  claim {live.claim_uri}")

    entries = (
        placement_entries(open_placement)
        + placement_entries(bound)
        + placement_entries(live)
    )
    catalogue = {
        "schema": "rsure.catalogue/v1",
        "networkId": status.get("networkId"),
        "shard": status.get("shardId"),
        "root": manifest["root_uri"],
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }
    args.catalogue.parent.mkdir(parents=True, exist_ok=True)
    args.catalogue.write_text(json.dumps(catalogue, indent=2) + "\n")

    seed = {
        "network": "devnet",
        "networkId": status.get("networkId"),
        "shard": status.get("shardId"),
        "root": manifest["root_uri"],
        "generatedAt": catalogue["generatedAt"],
        "placements": {
            "open": {
                "insured": open_placement.insured,
                "syndicate": open_placement.syndicate_uri,
                "broker": open_placement.broker_uri,
                "risk": open_placement.risk_uri,
                "slip": open_placement.slip_uri,
            },
            "bound": {
                "insured": bound.insured,
                "syndicate": bound.syndicate_uri,
                "broker": bound.broker_uri,
                "risk": bound.risk_uri,
                "slip": bound.slip_uri,
                "policy": bound.policy_uri,
                "settledClaim": settled,
            },
            "live": {
                "insured": live.insured,
                "syndicate": live.syndicate_uri,
                "broker": live.broker_uri,
                "risk": live.risk_uri,
                "slip": live.slip_uri,
                "policy": policy,
                "openClaim": live.claim_uri,
            },
        },
        "actors": {
            name: actors.address(name)
            for name in dict.fromkeys((open_placement.insured,
                                       open_placement.syndicate_owner,
                                       open_placement.platform))
        },
    }
    args.seed.parent.mkdir(parents=True, exist_ok=True)
    args.seed.write_text(json.dumps(seed, indent=2) + "\n")

    print("web_seed: ok")
    print(f"  catalogue {args.catalogue} ({len(entries)} entries)")
    print(f"  seed {args.seed}")
    print("  run `make web-build` so the app serves the new catalogue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
