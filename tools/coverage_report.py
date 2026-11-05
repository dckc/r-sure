#!/usr/bin/env python3
"""Report contract-behaviour coverage from the last suite run.

This is not Python line coverage. It reports which registered public arms were
actually asserted by passing suites, plus the core-flow/invariant/finding
coverage that the registers declare.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ARMS = ROOT / "audit" / "registers" / "arms.yaml"
TESTS = ROOT / "audit" / "registers" / "tests.yaml"
RESULTS = ROOT / "deployments" / "suite-results.json"
FLOWS = ROOT / "spec" / "flows" / "core.yaml"
FINDINGS = ROOT / "audit" / "registers" / "findings.yaml"
INVARIANTS = ROOT / "spec" / "invariants.md"
OUT_JSON = ROOT / "deployments" / "coverage.json"
OUT_MD = ROOT / "audit" / "traceability" / "coverage.md"


def load(path: Path):
    return yaml.safe_load(path.read_text()) if path.is_file() else {}


def measured() -> dict:
    results = load(RESULTS).get("results", []) if RESULTS.is_file() else []
    passing = [row for row in results if row.get("status") == "pass"]
    covered: set[str] = set()
    for row in passing:
        covered.update(row.get("covered_arms", []))
    return {"results": results, "passing": passing, "covered": covered}


def build() -> dict:
    arms_doc = load(ARMS)
    arms = arms_doc.get("arms", [])
    public = {f'{a["component"]}@"{a["arm"]}"' for a in arms
              if a.get("visibility") == "public"}
    all_arms = {f'{a["component"]}@"{a["arm"]}"' for a in arms}
    flows = load(FLOWS).get("rules", [])
    core = {rule["arm"] for rule in flows if rule.get("lean_status") == "proved-model"}
    findings = load(FINDINGS).get("findings", [])
    fixed = [f for f in findings if f.get("status") == "fixed"]
    invariants = []
    if INVARIANTS.is_file():
        import re
        invariants = re.findall(r"^\|\s*(INV-\d+)\s*\|", INVARIANTS.read_text(), re.M)
    data = measured()
    covered = data["covered"]
    payload = {
        "passing_suites": len(data["passing"]),
        "total_suites": len(data["results"]),
        "public_arms_asserted": sorted(public & covered),
        "public_arms_total": len(public),
        "all_arms_asserted": sorted(all_arms & covered),
        "all_arms_total": len(all_arms),
        "core_flows_asserted": sorted(core & covered),
        "core_flows_total": len(core),
        "fixed_findings": [f["id"] for f in fixed],
        "fixed_findings_total": len(fixed),
        "invariants": invariants,
    }
    return payload


def render(payload: dict) -> str:
    def pct(a: int, b: int) -> str:
        return f"{a}/{b} ({(100 * a / b):.1f}%)" if b else "0/0"

    lines = [
        "# Coverage report",
        "",
        "> **Status:** Generated from `deployments/suite-results.json`; not line coverage.",
        "",
        "| Metric | Covered |",
        "|---|---|",
        f"| Passed suites | {payload['passing_suites']}/{payload['total_suites']} |",
        f"| Public arms asserted by passing suites | "
        f"{pct(len(payload['public_arms_asserted']), payload['public_arms_total'])} |",
        f"| All registered arms asserted | "
        f"{pct(len(payload['all_arms_asserted']), payload['all_arms_total'])} |",
        f"| Core flow arms asserted | "
        f"{pct(len(payload['core_flows_asserted']), payload['core_flows_total'])} |",
        f"| Fixed findings with a regression run | "
        f"{len(payload['fixed_findings'])}/{payload['fixed_findings_total']} |",
        f"| Invariants tracked | {len(payload['invariants'])}/12 |",
        "",
        "A suite contributes only when it is `pass` and emits `covered_arms` in its",
        "`RSURE_RESULT` trailer. Stubs and zero-assertion suites contribute nothing.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    payload = build()
    text = render(payload)
    if args.write:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        OUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUT_MD.write_text(text)
        print(f"coverage: wrote {OUT_MD.relative_to(ROOT)}")
        return 0
    if args.check:
        if not OUT_MD.is_file() or OUT_MD.read_text() != text:
            print("coverage: report is stale; run --write", file=sys.stderr)
            return 1
        print(f"coverage: {payload['passing_suites']}/{payload['total_suites']} suites; "
              f"{len(payload['public_arms_asserted'])}/{payload['public_arms_total']} public arms")
        return 0
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
