#!/usr/bin/env python3
"""Validate `deployments/devnet.json` against the install order and registered components."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "deployments" / "devnet.json"
ORDER = [
    "00_root.rho", "01_kernel.rho", "02_admin.rho", "03_terms.rho", "04_math.rho",
    "05_rgen.rho", "40_payments.rho", "15_distribution.rho", "16_fund.rho",
    "10_syndicate.rho", "11_broker.rho", "12_risk.rho", "13_slip.rho", "14_line.rho",
    "17_policy.rho", "18_claim.rho", "19_books.rho",
]
EXPECTED_ROOTS = {"00_root.rho"}


def uris(value) -> list[str]:
    if isinstance(value, str):
        return [value] if value.startswith("rho:id:") else []
    if isinstance(value, (list, tuple)):
        return [uri for item in value for uri in uris(item)]
    if isinstance(value, dict):
        return [uri for item in value.values() for uri in uris(item)]
    return []


def main() -> int:
    if not MANIFEST.is_file():
        print(f"check-install-manifest: missing {MANIFEST}", file=sys.stderr)
        return 1
    doc = json.loads(MANIFEST.read_text())
    root = doc.get("root_uri")
    components = doc.get("components") or {}
    problems: list[str] = []
    if not isinstance(root, str) or not root.startswith("rho:id:"):
        problems.append(f"root_uri is not a rho:id URI: {root!r}")
    expected = [name for name in ORDER if name not in EXPECTED_ROOTS]
    missing = [name for name in expected if name not in components]
    extra = [name for name in components if name not in expected]
    if missing:
        problems.append(f"missing install records: {missing}")
    if extra:
        problems.append(f"unexpected install records: {extra}")
    seen: dict[str, str] = {}
    if isinstance(root, str):
        seen[root] = "00_root.rho"
    for name in expected:
        if name not in components:
            continue
        found = uris(components[name])
        if not found:
            problems.append(f"{name}: no registered rho:id URI")
        for uri in found:
            if uri in seen:
                problems.append(f"{name}: duplicate URI {uri} (also {seen[uri]})")
            seen[uri] = name
    for problem in problems:
        print(f"check-install-manifest: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"check-install-manifest: {len(components)} term(s), {len(seen)} unique URI(s), root {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
