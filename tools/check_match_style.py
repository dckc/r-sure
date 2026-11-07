#!/usr/bin/env python3
"""Enforce effective `match` use in the r-sure contracts.

Rules are hard failures; there is no warning channel:

* M-001: non-let dispatch depth > 3;
* M-002: same-enum `else if` ladder (one membership `||` test is allowed);
* M-003: a mutating match has no total arm;
* M-004: the total arm must repost the state cell and reply (or abort with 1/0);
* M-005: identical bodies, duplicate patterns, or a catch-all that is not last;
* M-006: a single `_`/lone-binder arm followed by a presence test on the scrutinee;
* M-007: a match token that could not be parsed;
* M-008: a match with no arms.

Report-only advice: A-001 map pattern without `..._`; A-002 duplicated class lists.

Run: `python3 tools/check_match_style.py --check` (gate), `--report`, `--self-test`, `--json`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import rholang_match as scan  # noqa: E402

SUPPRESS = re.compile(r"//\s*match-style:\s*allow\s+(M-\d{3})\s+(\S.*)$")


def suppressions(path: Path) -> tuple[dict[tuple[int, str], str], list[str]]:
    found: dict[tuple[int, str], str] = {}
    problems: list[str] = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if "match-style:" not in line:
            continue
        match = SUPPRESS.search(line)
        if not match:
            problems.append(f"{path.relative_to(ROOT)}:{number}: malformed suppression")
            continue
        found[(number, match.group(1))] = match.group(2).strip()
        found[(number + 1, match.group(1))] = match.group(2).strip()
    return found, problems


def collect() -> tuple[list[scan.Scan], dict, list[tuple[str, int, str, str]], list[str], int]:
    scans, _ = scan.scan_all()
    summary = scan.summary(scans)
    allowed: dict[tuple[str, int, str], str] = {}
    problems: list[str] = []
    suppressed = 0
    for file in scan.CONTRACT_ROOT.rglob("*.rho"):
        rel = str(file.relative_to(ROOT))
        found, malformed = suppressions(file)
        problems.extend(malformed)
        for (line, code), reason in found.items():
            allowed[(rel, line, code)] = reason
    violations: list[tuple[str, int, str, str]] = []
    for file, line, code, message in summary["violations"]:
        if (file, line, code) in allowed:
            suppressed += 1
            continue
        violations.append((file, line, code, message))
    return scans, summary, violations, problems, suppressed


def report(scans: list[scan.Scan], summary: dict, violations: list, problems: list,
           suppressed: int) -> int:
    print(f"check-match-style: {summary['files']} files, "
          f"{summary['match_sites']} match sites "
          f"({summary['lets']} let, {summary['dispatch']} dispatch), "
          f"{len(violations)} violation(s), {suppressed} suppression(s)")
    print(f"  depth histogram: {summary['depth_histogram']}")
    by_file: dict[str, int] = {}
    for item in scans:
        by_file[item.path] = item.match_count
    print("  per file: " + ", ".join(f"{name}={count}" for name, count in sorted(by_file.items())))
    for file, line, code, message in violations:
        print(f"{file}:{line}: {code}: {message}", file=sys.stderr)
    for problem in problems:
        print(f"{problem}", file=sys.stderr)
    for file, line, code, message in summary["advisories"]:
        print(f"advice {file}:{line}: {code}: {message}")
    return 1 if violations or problems else 0


def self_test() -> int:
    cells = {"riskState"}
    cases: list[tuple[str, str, list[str]]] = [
        ("masked", 'new x in { x!("match (a) { b => Nil }") }', []),
        ("let", 'new c in { contract C(a) = { match a { x => { Nil } } } }', []),
        ("for-depth", 'new c in { contract C(a) = { for (@x <- a) { match x { _ => { Nil } } } } }', []),
        ("depth-3", 'new c in { contract C(a) = { match a { _ => { match a { _ => { match a { _ => { Nil } } } } } } } }', []),
        ("depth-4", 'new c in { contract C(a) = { match a { _ => { match a { _ => { match a { _ => { match a { _ => { Nil } } } } } } } } } }', ["M-001"]),
        ("no-catch", 'new c in { contract C(a) = { for (@s <- state) { match a { (true, x) => { ret!(x) } } } } }', ["M-003"]),
        ("reply-only", 'new c in { contract C(a) = { for (@s <- state) { match a { _ => { ret!(true) } } } } }', ["M-004"]),
        ("repost-reply", 'new c in { contract C(a) = { for (@s <- state) { match a { _ => { state!(s) | ret!(true) } } } } }', []),
        ("abort", 'new c in { contract C(a) = { for (@s <- state) { match a { _ => { 1/0 } } } } }', []),
        ("identical", 'new c in { contract C(a) = { match a { "a" => { ret!(1) } "b" => { ret!(1) } _ => { ret!(0) } } } }', ["M-005"]),
        ("duplicate", 'new c in { contract C(a) = { match a { "a" => { ret!(1) } "a" => { ret!(2) } _ => { ret!(0) } } } }', ["M-005"]),
        ("dead-wild", 'new c in { contract C(a) = { match a { _ => { if (a != Nil) { ret!(1) } else { ret!(0) } } } } }', ["M-006"]),
        ("membership", 'new c in { contract C(a) = { if (a == "x" || a == "y") { ret!(1) } else { ret!(0) } } }', []),
        ("ladder", 'new c in { contract C(a) = { if (a == "x") { ret!(1) } else if (a == "y") { ret!(2) } else { ret!(0) } } }', ["M-002"]),
    ]
    failed = 0
    for name, text, expected in cases:
        result = scan.scan_text(text, f"<{name}>", cells)
        got = [code for item in result.constructs for code, _ in item.violations]
        got += ["M-007"] if result.parse_errors else []
        if sorted(set(got)) != sorted(set(expected)):
            print(f"self-test {name}: expected {expected}, got {sorted(set(got))}",
                  file=sys.stderr)
            failed += 1
    if failed:
        return 1
    print(f"check-match-style: self-test: {len(cases)} fixture groups passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    scans, summary, violations, problems, suppressed = collect()
    if args.json:
        print(json.dumps({**summary, "violations": violations,
                          "suppressed": suppressed, "problems": problems}, indent=2))
        return 1 if violations or problems else 0
    if args.report:
        return report(scans, summary, violations, problems, suppressed)
    # default and --check
    result = report(scans, summary, violations, problems, suppressed)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
