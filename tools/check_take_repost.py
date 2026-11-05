#!/usr/bin/env python3
"""Flag a second consume of the same state cell with no intervening repost.

Heuristic for the P0 liveness defect: `for (@s <- cell)` consumes the only datum; a later
`for (@s2 <- cell)` on the same path blocks forever unless the first snapshot was reposted.
Only state cells declared in contracts/components.json are considered.
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
CONTRACT = re.compile(r"^\s*contract\s+([A-Za-z_]\w*)\s*\(", re.M)
CONSUME = re.compile(r"for\s*\(\s*@?[A-Za-z_]\w*\s*<-\s*([A-Za-z_]\w*)\s*\)")
WATCHED = {
    ("Syndicate", "openLine"),
    ("Slip", "bind"),
    ("Policy", "distribute"),
    ("Policy", "openClaim"),
    ("Policy", "settleClaim"),
    ("Claim", "settle"),
    ("Claim", "dispute"),
    ("Distribution", "run"),
}


def state_cells() -> set[str]:
    document = json.loads(COMPONENTS.read_text())
    cells: set[str] = set()
    for entry in document.get("components", {}).values():
        cells.update(entry.get("state_cells", []))
    return cells


def bodies(text: str):
    """Yield (name, start_line, body) using brace matching from each contract header."""
    for match in CONTRACT.finditer(text):
        brace = text.find("{", match.end())
        if brace < 0:
            continue
        depth = 0
        end = None
        for index in range(brace, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            continue
        yield match.group(1), text.count("\n", 0, match.start()) + 1, text[match.start():end]


def strip_nested_contracts(body: str) -> str:
    out = body
    for match in list(CONTRACT.finditer(body))[1:]:
        brace = body.find("{", match.end())
        if brace < 0:
            continue
        depth = 0
        end = None
        for index in range(brace, len(body)):
            if body[index] == "{":
                depth += 1
            elif body[index] == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end:
            out = out[:match.start()] + " " * (end - match.start()) + out[end:]
    return out


def depth_at(text: str, pos: int) -> int:
    depth = 0
    for char in text[:pos]:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
    return depth


def qualifies(text: str, start: int, end: int, cell: str, base_depth: int) -> bool:
    for match in re.finditer(rf"\b{re.escape(cell)}\s*!\s*\(", text[start:end]):
        if depth_at(text, start + match.start()) <= base_depth:
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args(argv)

    cells = state_cells()
    problems: list[str] = []
    for path in sorted(DEPLOY.glob("*.rho")):
        text = path.read_text()
        for name, start_line, body in bodies(text):
            body = strip_nested_contracts(body)
            sites: dict[str, list[tuple[int, int]]] = {}
            for match in CONSUME.finditer(body):
                cell = match.group(1)
                if cell not in cells:
                    continue
                line = start_line + body.count("\n", 0, match.start())
                sites.setdefault(cell, []).append((line, match.start()))
            arm_match = re.search(r'contract\s+[A-Za-z_]\w*\s*\(\s*@?"([^"]+)"', body)
            arm = arm_match.group(1) if arm_match else ""
            if (name, arm) not in WATCHED:
                continue
            for cell, found in sites.items():
                for (line1, pos1), (line2, pos2) in zip(found, found[1:]):
                    if not qualifies(body, pos1, pos2, cell, depth_at(body, pos1)):
                        problems.append(
                            f"{name}@\"{arm}\": second consume of {cell} at line {line2} "
                            f"(first at line {line1}) without an intervening repost")

    if args.report:
        out = ROOT / "audit" / "evidence" / "2026-11-05-concurrency-tabletop"
        out.mkdir(parents=True, exist_ok=True)
        (out / "take-repost.txt").write_text("\n".join(problems) + "\n")
        print(f"take-repost: wrote {len(problems)} candidate(s)")
        return 0

    for problem in problems:
        print(f"take-repost: {problem}", file=sys.stderr)
    if problems:
        print(f"take-repost: {len(problems)} candidate(s)", file=sys.stderr)
        return 1
    print("take-repost: no second consume without a repost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
