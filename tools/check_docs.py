#!/usr/bin/env python3
"""Lightweight docs gate: SUMMARY coverage, relative links and deploy-file coverage."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SUMMARY = DOCS / "SUMMARY.md"
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
DEPLOY = ROOT / "contracts" / "src" / "deploy"


def main() -> int:
    errors: list[str] = []
    if not SUMMARY.is_file():
        print("check-docs: missing docs/SUMMARY.md", file=sys.stderr)
        return 1
    text = SUMMARY.read_text()
    listed = []
    for match in LINK.finditer(text):
        target = match.group(1)
        if target.startswith("http") or target.startswith("#"):
            continue
        path = (DOCS / target).resolve()
        listed.append(path)
        if not path.is_file():
            errors.append(f"SUMMARY.md: missing {target}")

    chapters = {p.resolve() for p in DOCS.rglob("*.md") if p.name != "SUMMARY.md"}
    listed_set = set(listed)
    for chapter in sorted(chapters - listed_set):
        errors.append(f"{chapter.relative_to(ROOT)}: not listed in SUMMARY.md")
    for chapter in sorted(listed_set - chapters):
        if chapter != SUMMARY.resolve():
            errors.append(f"SUMMARY.md: lists non-chapter {chapter.relative_to(ROOT)}")

    seen: dict[Path, int] = {}
    for path in listed:
        seen[path] = seen.get(path, 0) + 1
    for path, count in seen.items():
        if count > 1:
            errors.append(f"SUMMARY.md: {path.relative_to(ROOT)} listed {count} times")

    for md in DOCS.rglob("*.md"):
        for number, line in enumerate(md.read_text().splitlines(), 1):
            for match in LINK.finditer(line):
                target = match.group(1)
                if target.startswith("http") or target.startswith("#") or target.endswith(".pdf"):
                    continue
                if not (md.parent / target).resolve().is_file():
                    errors.append(f"{md.relative_to(ROOT)}:{number}: broken link {target}")

    contract_map = (DOCS / "reference" / "contract-map.md").read_text()
    for deploy in sorted(DEPLOY.glob("*.rho")):
        if deploy.name not in contract_map:
            errors.append(f"reference/contract-map.md: missing {deploy.name}")

    if errors:
        for error in errors:
            print(f"check-docs: {error}", file=sys.stderr)
        return 1
    print(f"check-docs: {len(chapters)} chapters, links and deploy coverage okay")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
