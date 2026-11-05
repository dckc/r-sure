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


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def measured() -> dict:
    results = load(RESULTS).get("results", []) if RESULTS.is_file() else []
    passing = [
        row for row in results
        if row.get("status") == "pass"
        and _int(row.get("assertions", 0)) > 0
        and _int(row.get("failed", 0)) == 0
    ]
    covered: set[str] = set()
    covered_by: dict[str, set[str]] = {}
    for row in passing:
        for arm in row.get("covered_arms") or []:
            if not isinstance(arm, str):
                continue
            covered.add(arm)
            covered_by.setdefault(arm, set()).add(row.get("suite"))
    return {"results": results, "passing": passing, "covered": covered,
            "covered_by": covered_by}


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
    covered_by = data["covered_by"]
    tests = load(TESTS).get("tests", [])
    registered = {row.get("name") for row in tests if isinstance(row, dict)}
    passing = [row for row in data["passing"]
               if not registered or row.get("suite") in registered]

    # A fixed finding counts only when a passing suite with assertions asserted one of
    # the finding's linked arms.  Nothing has run => nothing is verified.
    verified = []
    regression_suites: dict[str, list[str]] = {}
    for finding in fixed:
        linked = [arm for arm in finding.get("arms", []) if arm in covered]
        if linked:
            verified.append(finding["id"])
            suites: set[str] = set()
            for arm in linked:
                suites.update(covered_by.get(arm, set()))
            regression_suites[finding["id"]] = sorted(suites)
    verified_ids = {finding["id"] for finding in fixed
                    if finding["id"] in verified}

    payload = {
        "passing_suites": len(passing),
        "total_suites": len(tests) if tests else len(data["results"]),
        "public_arms_asserted": sorted(public & covered),
        "public_arms_total": len(public),
        "all_arms_asserted": sorted(all_arms & covered),
        "all_arms_total": len(all_arms),
        "core_flows_asserted": sorted(core & covered),
        "core_flows_total": len(core),
        "fixed_findings": verified,
        "fixed_findings_total": len(fixed),
        "fixed_findings_unverified": sorted(
            finding["id"] for finding in fixed
            if finding["id"] not in verified_ids),
        "fixed_findings_regression_suites": regression_suites,
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
        f"| Fixed findings with a passing regression suite asserting a linked arm | "
        f"{len(payload['fixed_findings'])}/{payload['fixed_findings_total']} |",
        f"| Invariants tracked | {len(payload['invariants'])}/12 |",
        "",
        "A suite contributes only when it is `pass`, has at least one assertion and",
        "emits `covered_arms` in its `RSURE_RESULT` trailer. Stubs and zero-assertion",
        "suites contribute nothing. A fixed finding is counted only when a linking arm",
        "appears in that asserted set, so the metric is zero before any suite runs.",
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
