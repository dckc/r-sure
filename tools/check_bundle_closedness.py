#!/usr/bin/env python3
"""Heuristic check for `bundle+{*X}` publications whose contract body captures a
non-local state cell or capability. A bundle must be closed; the node rejects a bundle with
free variables or wildcards at deploy time.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "contracts" / "src" / "deploy"
COMPONENTS = ROOT / "contracts" / "components.json"
BUNDLE = re.compile(r"bundle\+\s*\{\s*\*([A-Za-z_]\w*)\s*\}")
CONTRACT = re.compile(r"^\s*contract\s+([A-Za-z_]\w*)\s*\(([^)]*)\)", re.M)
INSTANCE_BUNDLES = {"LineGrant", "Syndicate", "Line", "Slip", "Policy", "Claim",
                    "Distribution", "Broker", "Risk"}
CAPTURES = {
    "purse", "issuer", "slipToken", "policyToken", "claimToken", "creditCap",
    "settleCap", "releaseCap", "policyUri", "rcashRootUri", "rgenRootUri",
}


def state_cells() -> set[str]:
    document = json.loads(COMPONENTS.read_text())
    cells: set[str] = set()
    for entry in document.get("components", {}).values():
        cells.update(entry.get("state_cells", []))
    return cells


def contract_body(text: str, name: str) -> tuple[str, str] | None:
    for match in CONTRACT.finditer(text):
        if match.group(1) != name:
            continue
        brace = text.find("{", match.end())
        if brace < 0:
            continue
        depth = 0
        for index in range(brace, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return match.group(2), text[brace:index + 1]
    return None


def bound_names(params: str, body: str) -> set[str]:
    names = set(re.findall(r"@?([A-Za-z_]\w*)", params))
    for new in re.finditer(r"\bnew\s+([^;{}]*?)\s+in\b", body):
        names.update(re.findall(r"[A-Za-z_]\w*", new.group(1)))
    for receive in re.finditer(r"for\s*\(([^)]*?)\s*<-", body):
        names.update(re.findall(r"@?([A-Za-z_]\w*)", receive.group(1)))
    names.update(re.findall(r"contract\s+([A-Za-z_]\w*)", body))
    return names


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args(argv)

    cells = state_cells()
    problems: list[str] = []
    for path in sorted(DEPLOY.glob("*.rho")):
        text = path.read_text()
        for bundle in BUNDLE.finditer(text):
            name = bundle.group(1)
            if name not in INSTANCE_BUNDLES:
                continue
            found = contract_body(text, name)
            if not found:
                continue
            params, body = found
            bound = bound_names(params, body)
            for cell in sorted(cells | CAPTURES):
                if cell in bound:
                    continue
                if re.search(rf"\b{re.escape(cell)}\b", body):
                    line = text.count("\n", 0, bundle.start()) + 1
                    problems.append(
                        f"{path.name}:{line}: bundle+{{*{name}}} captures {cell} "
                        "not bound inside the contract")

    if args.report:
        out = ROOT / "audit" / "evidence" / "2026-11-05-concurrency-tabletop"
        out.mkdir(parents=True, exist_ok=True)
        (out / "bundle-closedness.txt").write_text("\n".join(problems) + "\n")
        print(f"bundle-closedness: wrote {len(problems)} candidate(s)")
        return 0

    for problem in problems:
        print(f"bundle-closedness: {problem}", file=sys.stderr)
    if problems:
        print(f"bundle-closedness: {len(problems)} candidate(s)", file=sys.stderr)
        return 1
    print("bundle-closedness: no captured state/capability found in a bundle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
