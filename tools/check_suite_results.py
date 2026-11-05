#!/usr/bin/env python3
"""Reconcile the test register with the last suite run.

A suite may only be ``passing`` when a real run passed with enough assertions and
declared at least one covered arm.  ``not_run`` needs a concrete environment reason;
a stub cannot masquerade as coverage and a register row cannot claim a pass that never
ran.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "audit" / "registers" / "tests.yaml"
ARMS = ROOT / "audit" / "registers" / "arms.yaml"
RESULTS = ROOT / "deployments" / "suite-results.json"
STATUS = {"pass": "passing", "fail": "failing", "not_run": "not_run"}
DEFAULT_MIN_ASSERTIONS = 3


def load_results() -> dict[str, dict]:
    if not RESULTS.is_file():
        return {}
    try:
        doc = json.loads(RESULTS.read_text())
    except ValueError:
        return {}
    return {row.get("suite"): row for row in doc.get("results", [])
            if isinstance(row, dict) and row.get("suite")}


def registered_arms() -> set[str]:
    if not ARMS.is_file():
        return set()
    doc = yaml.safe_load(ARMS.read_text()) or {}
    return {
        f'{arm["component"]}@"{arm["arm"]}"'
        for arm in doc.get("arms", [])
        if isinstance(arm, dict) and "component" in arm and "arm" in arm
    }


def real_run(row: dict) -> bool:
    """A row is a run only if it was started and has an observed return code."""
    return bool(row.get("started_at")) and row.get("returncode") is not None


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail on a register/run mismatch")
    ap.add_argument("--require", action="store_true",
                    help="fail when any registered suite has no run")
    ap.add_argument("--write", action="store_true",
                    help="write statuses from the run")
    args = ap.parse_args(argv)

    if not REGISTER.is_file():
        print(f"check-suite-results: missing {REGISTER}", file=sys.stderr)
        return 2
    doc = yaml.safe_load(REGISTER.read_text()) or {}
    tests = doc.get("tests", [])
    results = load_results()
    arms = registered_arms()

    errors: list[str] = []
    mismatches: list[str] = []
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
        current = test.get("status", "not_run")
        result = results.get(name)
        if result is None:
            if current == "passing":
                errors.append(f"{name}: register says passing but there is no run")
            elif args.require:
                errors.append(f"{name}: no run recorded (--require)")
            if args.write and current != "not_run":
                test["status"] = "not_run"
                changed = True
            continue

        if not real_run(result):
            errors.append(f"{name}: result row is not a real run")
            continue

        expected = STATUS.get(result.get("status"), "not_run")
        minimum = _int(test.get("min_assertions", DEFAULT_MIN_ASSERTIONS))

        if expected == "not_run":
            reason = (result.get("env_reason") or "").strip()
            if not reason:
                errors.append(f"{name}: not_run without an environment reason")
        elif expected == "passing":
            assertions = _int(result.get("assertions", 0))
            if assertions < minimum:
                errors.append(
                    f"{name}: passing with {assertions} assertions "
                    f"(minimum {minimum})")
            if _int(result.get("returncode", 1)) != 0:
                errors.append(
                    f"{name}: passing with returncode {result.get('returncode')}")
            if _int(result.get("failed", 0)) != 0:
                errors.append(
                    f"{name}: passing with {result.get('failed')} failed assertions")
            covered = result.get("covered_arms") or []
            if not isinstance(covered, list) or not covered:
                errors.append(f"{name}: passing without covered_arms")
            elif arms:
                unknown = sorted(set(covered) - arms)
                if unknown:
                    errors.append(
                        f"{name}: covered_arms not in arms.yaml: {unknown}")
        elif expected == "failing":
            if _int(result.get("assertions", 0)) == 0 and not result.get("env_reason"):
                errors.append(f"{name}: failing without an explanation")

        if current != expected:
            mismatches.append(f"{name}: register={current} run={expected}")
            if args.write:
                test["status"] = expected
                changed = True

    if args.write and changed:
        REGISTER.write_text(yaml.dump(doc, sort_keys=False, default_flow_style=False))
        print("check-suite-results: updated tests.yaml from the run")

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"check-suite-results: {error}", file=sys.stderr)
    if args.check:
        for mismatch in mismatches:
            print(f"check-suite-results: {mismatch}", file=sys.stderr)
        if mismatches:
            errors.append("register does not match the run")

    print(f"check-suite-results: {len(tests)} register rows, {len(results)} run rows")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
