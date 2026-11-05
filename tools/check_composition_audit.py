#!/usr/bin/env python3
"""Enforce the composition interface table and resolve its hazard/finding links."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "audit" / "composition"
REGISTERS = ROOT / "audit" / "registers"
REQUIRED = {"id", "caller", "callee", "arm", "call_site", "request", "success_reply",
            "refusal_reply", "awaits", "state_held", "atomicity", "capabilities",
            "verdict"}
REQUIRED_CALLEES = {
    "SureRoot", "Clock", "Payments", "RgenAdapter", "Syndicate", "LineGrant",
    "LineFactory", "BrokerBook", "RiskBook", "Slip", "Line", "Distribution",
    "SureFund", "Policy", "Claim", "PolicyBook", "ClaimBook", "CoverTerms", "SureMath",
}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def main() -> int:
    document = load(AUDIT / "interfaces.yaml")
    interfaces = document.get("interfaces", [])
    hazards = {h.get("id") for h in load(REGISTERS / "hazards.yaml").get("hazards", [])}
    findings = {f.get("id") for f in load(REGISTERS / "findings.yaml").get("findings", [])}
    problems: list[str] = []
    ids: set[str] = set()
    callees: set[str] = set()
    for entry in interfaces:
        ident = entry.get("id")
        if not ident or ident in ids:
            problems.append(f"bad or duplicate id {ident!r}")
        ids.add(ident)
        for field in REQUIRED:
            if field not in entry:
                problems.append(f"{ident}: missing {field}")
        callees.add(str(entry.get("callee", "")).split("/")[0].strip())
        for hazard in entry.get("hazards", []) or []:
            if hazard not in hazards:
                problems.append(f"{ident}: dangling hazard {hazard}")
        for finding in entry.get("findings", []) or []:
            if finding not in findings:
                problems.append(f"{ident}: dangling finding {finding}")

    for callee in sorted(REQUIRED_CALLEES - callees):
        problems.append(f"no interface names {callee} as a callee")

    print(f"check-composition-audit: {len(interfaces)} interfaces, {len(ids)} ids, "
          f"{len(REQUIRED_CALLEES)} required callees")
    for problem in problems:
        print(f"check-composition-audit: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
