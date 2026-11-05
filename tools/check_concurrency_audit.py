#!/usr/bin/env python3
"""Enforce one concurrency review per component and resolve hazard/finding links."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
COMPONENTS = ROOT / "contracts" / "components.json"
AUDIT = ROOT / "audit" / "concurrency"
REGISTERS = ROOT / "audit" / "registers"
VERDICTS = {"safe-by-inspection", "concern", "finding", "not-applicable"}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def main() -> int:
    import json
    catalogue = json.loads(COMPONENTS.read_text()).get("components", {})
    document = load_yaml(AUDIT / "components.yaml")
    rows = {row.get("component"): row for row in document.get("components", [])}
    hazards = {h.get("id") for h in load_yaml(REGISTERS / "hazards.yaml").get("hazards", [])}
    findings = {f.get("id") for f in load_yaml(REGISTERS / "findings.yaml").get("findings", [])}
    problems: list[str] = []

    for name in catalogue:
        row = rows.get(name)
        if not row:
            problems.append(f"{name}: no concurrency row")
            continue
        if row.get("verdict") not in VERDICTS:
            problems.append(f"{name}: bad verdict {row.get('verdict')!r}")
        review = AUDIT / str(row.get("review", ""))
        if not review.is_file():
            problems.append(f"{name}: missing review {review}")
        for hazard in row.get("hazards", []) or []:
            if hazard not in hazards:
                problems.append(f"{name}: dangling hazard {hazard}")
        for finding in row.get("findings", []) or []:
            if finding not in findings:
                problems.append(f"{name}: dangling finding {finding}")

    for name in rows:
        if name not in catalogue:
            problems.append(f"{name}: concurrency row has no catalogue component")

    print(f"check-concurrency-audit: {len(rows)} reviewed, {len(catalogue)} catalogue "
          f"components, {len(hazards)} hazards, {len(findings)} findings")
    for problem in problems:
        print(f"check-concurrency-audit: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
