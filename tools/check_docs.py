#!/usr/bin/env python3
"""Documentation gate: SUMMARY coverage, links, status labels, paper manifest, deploy map."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SUMMARY = DOCS / "SUMMARY.md"
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
STATUS = re.compile(r"^>\s*\*\*Status:\*\*", re.M)
H1 = re.compile(r"^#\s+\S", re.M)
CHAPTER_DIRS = {"orientation", "primer", "concepts", "case-studies", "guides",
                "reference", "appendix"}
PAPER_DIR = DOCS / "papers"
DEPLOY = ROOT / "contracts" / "src" / "deploy"
MIN_BODY = {"primer": 800, "concepts": 600, "case-studies": 600}


def non_space(text: str) -> int:
    return sum(1 for ch in text if not ch.isspace())


def main() -> int:
    errors: list[str] = []
    if not SUMMARY.is_file():
        print("check-docs: missing docs/SUMMARY.md", file=sys.stderr)
        return 1
    text = SUMMARY.read_text()
    listed: list[Path] = []
    for match in LINK.finditer(text):
        target = match.group(1)
        if target.startswith("http") or target.startswith("#"):
            continue
        path = (DOCS / target).resolve()
        listed.append(path)
        if not path.is_file():
            errors.append(f"SUMMARY.md: missing {target}")

    chapters = {
        p.resolve()
        for p in DOCS.rglob("*.md")
        if p.name != "SUMMARY.md" and PAPER_DIR not in p.parents
    }
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
        body = md.read_text()
        rel = md.relative_to(ROOT)
        for number, line in enumerate(body.splitlines(), 1):
            for match in LINK.finditer(line):
                target = match.group(1)
                if target.startswith("http") or target.startswith("#") or target.endswith(".pdf"):
                    continue
                if not (md.parent / target).resolve().is_file():
                    errors.append(f"{rel}:{number}: broken link {target}")
        if PAPER_DIR in md.parents or md.resolve() == SUMMARY.resolve():
            continue
        top = md.parent.name
        if top in CHAPTER_DIRS:
            if not H1.search(body):
                errors.append(f"{rel}: missing H1")
            if not STATUS.search(body[:2000]):
                errors.append(f"{rel}: missing status label near the top")
        if top in MIN_BODY and non_space(body) < MIN_BODY[top]:
            errors.append(f"{rel}: body too short for a {top} chapter")
        for bad in ("/home/patrick/", "C:\\"):
            if bad in body:
                errors.append(f"{rel}: absolute local path {bad}")

    readme = (ROOT / "README.md").read_text()
    for bad in ("/home/patrick/", "C:\\"):
        if bad in readme:
            errors.append(f"README.md: absolute local path {bad}")

    manifest_path = PAPER_DIR / "manifest.json"
    if not manifest_path.is_file():
        errors.append("docs/papers/manifest.json: missing")
    else:
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"docs/papers/manifest.json: {exc}")
        else:
            for paper in manifest.get("papers", []):
                path = PAPER_DIR / paper.get("file", "")
                if not path.is_file():
                    errors.append(f"papers: missing {paper.get('file')}")
                    continue
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if digest != paper.get("sha256"):
                    errors.append(f"papers: sha256 mismatch for {paper.get('file')}")
                extract = PAPER_DIR / paper.get("extract", "")
                if not extract.is_file():
                    errors.append(f"papers: missing extract {paper.get('extract')}")

    contract_map = (DOCS / "reference" / "contract-map.md").read_text()
    for deploy in sorted(DEPLOY.glob("*.rho")):
        if deploy.name not in contract_map:
            errors.append(f"reference/contract-map.md: missing {deploy.name}")

    if errors:
        for error in errors:
            print(f"check-docs: {error}", file=sys.stderr)
        return 1
    print(f"check-docs: {len(chapters)} chapters, links, status labels, paper hash and deploy "
          "coverage okay")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
