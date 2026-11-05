#!/usr/bin/env python3
"""Reconcile the test register with the last suite run.

A suite may only be `passing` when the run actually passed with assertions.
`not_run` needs a concrete reason; a stub cannot masquerade as coverage.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "audit" / "registers" / "tests.yaml"
RESULTS = ROOT / "deployments" / "suite-results.json"
STATUS = {"pass": "passing", "fail": "failing", "not_run": "not_run"}


def load_results() -> dict[str, dict]:
    if not RESULTS.is_file():
        return {}
    doc = json.loads(RESULTS.read_text())
    return {row["suite"]: row for row in doc.get("results", [])}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail on a mismatch")
    ap.add_argument("--require", action="store_true", help="fail when no run exists")
    ap.add_argument("--write", action="store_true", help="write statuses from the run")
    args = ap.parse_args(argv)

    if not REGISTER.is_file():
        print(f"check-suite-results: missing {REGISTER}", file=sys.stderr)
        return 2
    doc = yaml.safe_load(REGISTER.read_text())
    tests = doc.get("tests", [])
    results = load_results()

    errors: list[str] = []
    warnings: list[str] = []
    if not results:
        message = f"no suite run at {RESULTS.relative_to(ROOT)}"
        if args.require:
            errors.append(message)
        else:
            warnings.append(message)

    changed = False
    for test in tests:
        name = test.get("name")
        current = test.get("status")
        result = results.get(name)
        if result is None:
            if current in {"passing", "failing"}:
                errors.append(f"{name}: register says {current} but there is no run")
            continue
        expected = STATUS.get(result.get("status"), "not_run")
        if expected == "not_run" and not result.get("env_reason"):
            errors.append(f"{name}: not_run without an environment reason")
        if expected == "passing":
            minimum = int(test.get("min_assertions", 3))
            if int(result.get("assertions", 0)) < minimum:
                errors.append(
                    f"{name}: passing with {result.get('assertions', 0)} assertions "
                    f"(minimum {minimum})")
        if args.write and current != expected:
            test["status"] = expected
            changed = True
        elif current != expected:
            errors.append(f"{name}: register={current} run={expected}")

    if args.write and changed:
        REGISTER.write_text(yaml.dump(doc, sort_keys=False, default_flow_style=False))
        print("check-suite-results: updated tests.yaml from the run")

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"check-suite-results: {error}", file=sys.stderr)
    if errors and args.check:
        return 1
    print(f"check-suite-results: {len(tests)} register rows, {len(results)} run rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
