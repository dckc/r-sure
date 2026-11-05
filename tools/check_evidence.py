#!/usr/bin/env python3
"""Validate the evidence manifests (`rsure.evidence/v2`).

An evidence manifest is a claim about what was run. The checker fails on a missing
required field, a dangling artifact, a hash or size mismatch, a result that does not say
whether it ran, and an evidence set with no stated limitation. It does not decide whether
the evidence is sufficient for a finding; the RCA and finding registers do that.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "audit" / "evidence"
SCHEMA = "rsure.evidence/v2"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = ("schema", "id", "date", "kind", "commit", "scope", "artifacts",
            "commands", "results", "limitations")
SCOPE_KEYS = ("audit", "production", "dynamic")
UNEXECUTED = ("not_run", "not-run", "partial", "blocked", "fail")


def resolve(path_text: str, manifest_dir: Path) -> Path:
    candidate = Path(path_text)
    if candidate.is_absolute():
        return candidate
    local = manifest_dir / candidate
    if local.exists():
        return local
    return ROOT / candidate


def want_reason(value: str) -> bool:
    text = str(value).strip().lower()
    return any(text.startswith(prefix) for prefix in UNEXECUTED)


def check_manifest(path: Path, problems: list[str]) -> dict | None:
    label = path.parent.name
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        problems.append(f"{label}: invalid JSON: {error}")
        return None

    for field in REQUIRED:
        if field not in doc:
            problems.append(f"{label}: missing {field}")
    if doc.get("schema") != SCHEMA:
        problems.append(f"{label}: schema {doc.get('schema')!r} is not {SCHEMA}")
    if doc.get("id") != label:
        problems.append(f"{label}: id {doc.get('id')!r} does not match directory")
    if not str(doc.get("date", "")).strip():
        problems.append(f"{label}: empty date")
    if not str(doc.get("commit", "")).strip():
        problems.append(f"{label}: empty commit")

    scope = doc.get("scope") or {}
    for key in SCOPE_KEYS:
        if key not in scope:
            problems.append(f"{label}: scope missing {key}")
    if scope.get("audit") not in {"internal", "independent"}:
        problems.append(f"{label}: bad scope.audit {scope.get('audit')!r}")
    if scope.get("production") is not False:
        problems.append(f"{label}: scope.production must be false; no production claim")
    if not str(scope.get("dynamic", "")).strip():
        problems.append(f"{label}: scope.dynamic is empty")

    artifacts = doc.get("artifacts") or []
    if not artifacts:
        problems.append(f"{label}: no artifacts")
    seen: set[str] = set()
    for artifact in artifacts:
        for field in ("path", "role", "sha256", "bytes", "description"):
            if field not in artifact:
                problems.append(f"{label}: artifact missing {field}")
        rel = artifact.get("path")
        if not rel:
            continue
        if rel in seen:
            problems.append(f"{label}: duplicate artifact {rel}")
        seen.add(rel)
        target = resolve(rel, path.parent)
        if not target.is_file():
            problems.append(f"{label}: artifact does not exist: {rel}")
            continue
        digest = artifact.get("sha256", "")
        if not SHA256.match(str(digest)):
            problems.append(f"{label}: artifact {rel}: bad sha256")
        else:
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != digest:
                problems.append(f"{label}: artifact {rel}: sha256 mismatch")
        if artifact.get("bytes") != target.stat().st_size:
            problems.append(f"{label}: artifact {rel}: byte size mismatch")

    if not doc.get("commands"):
        problems.append(f"{label}: no commands")
    results = doc.get("results") or {}
    if not results:
        problems.append(f"{label}: no results")
    reasons = doc.get("reasons") or {}
    for key, value in results.items():
        if want_reason(str(value)) and key not in reasons:
            problems.append(f"{label}: result {key} is {value!r} without a reason")
    for key in reasons:
        if key not in results:
            problems.append(f"{label}: reason for unknown result {key}")

    limitations = doc.get("limitations") or []
    if not limitations:
        problems.append(f"{label}: no limitations")
    if not all(isinstance(item, str) and item.strip() for item in limitations):
        problems.append(f"{label}: limitations must be non-empty strings")

    claim_text = " ".join(
        [str(doc.get("kind", "")), str(scope.get("note", ""))]
        + [str(value) for value in results.values()]
    ).lower()
    for phrase in ("production-ready", "production ready", "production-safe",
                   "production safe", "certified"):
        if phrase in claim_text:
            problems.append(f"{label}: forbidden production claim {phrase!r}")

    return {"id": label, "artifacts": len(artifacts), "results": len(results)}


def main() -> int:
    problems: list[str] = []
    manifests = sorted(EVIDENCE.glob("*/manifest.json"))
    if not manifests:
        print("check-evidence: no evidence manifests", file=sys.stderr)
        return 1

    summaries = []
    for path in manifests:
        summary = check_manifest(path, problems)
        if summary:
            summaries.append(summary)

    for directory in sorted(p for p in EVIDENCE.iterdir() if p.is_dir()):
        files = [p for p in directory.rglob("*") if p.is_file() and p.name != ".gitkeep"]
        if files and not (directory / "manifest.json").is_file():
            problems.append(f"{directory.name}: evidence files without manifest.json")

    for summary in summaries:
        print(f"check-evidence: {summary['id']}: {summary['artifacts']} artifacts, "
              f"{summary['results']} results")
    for problem in problems:
        print(f"check-evidence: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
