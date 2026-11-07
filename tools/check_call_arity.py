#!/usr/bin/env python3
"""Check that calls to locally defined contracts pass the declared arity.

A Rholang contract invocation whose argument count differs from the parameter list does
not reduce: the send simply does not match, and the caller waits forever. The parser and
the normalizer accept it, so this static check is the gate.

The checker reads contract definitions and sends in the same file. Names defined elsewhere
(components resolved from the registry, names received from a caller) are skipped.

Run: `python3 tools/check_call_arity.py` (exit 1 on a mismatch).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import rholang_match as scan  # noqa: E402

CONTRACT = re.compile(r"\bcontract\s+([A-Za-z_][A-Za-z0-9_']*)\s*\(")
SEND = re.compile(r"(?<![\w'])(@|\*)?\b([A-Za-z_][A-Za-z0-9_']*)\s*!\s*\(")


def split_ranges(masked: str, start: int, end: int) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    segment = start
    brace = paren = bracket = 0
    index = start
    while index < end:
        char = masked[index]
        if char == "{":
            brace += 1
        elif char == "}":
            brace = max(0, brace - 1)
        elif char == "(":
            paren += 1
        elif char == ")":
            paren = max(0, paren - 1)
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket = max(0, bracket - 1)
        elif char == "," and brace == paren == bracket == 0:
            ranges.append((segment, index))
            segment = index + 1
        index += 1
    ranges.append((segment, end))
    return ranges


def count_args(masked: str, raw: str, open_at: int) -> int:
    close_at = scan.matching(masked, open_at, "(", ")")
    if close_at < 0:
        return -1
    # Strings are blanked in `masked`; use the raw slice to decide whether a segment is
    # an argument so a literal first argument still counts.
    return sum(1 for start, end in split_ranges(masked, open_at + 1, close_at)
               if raw[start:end].strip())


def scan_file(path: Path) -> list[str]:
    text = path.read_text()
    masked = scan.mask(text)
    arities: dict[str, set[int]] = {}
    for match in CONTRACT.finditer(masked):
        open_at = match.end() - 1
        count = count_args(masked, text, open_at)
        if count >= 0:
            arities.setdefault(match.group(1), set()).add(count)
    problems: list[str] = []
    rel = str(path.relative_to(ROOT))
    for match in SEND.finditer(masked):
        name = match.group(2)
        if name not in arities:
            continue
        open_at = match.end() - 1
        count = count_args(masked, text, open_at)
        if count < 0:
            continue
        if count not in arities[name]:
            expected = "/".join(str(item) for item in sorted(arities[name]))
            problems.append(
                f"{rel}:{scan.line_of(masked, match.start())}: "
                f"{name}! passes {count} argument(s), contract takes {expected}")
    return problems


def main() -> int:
    roots = [ROOT / "contracts" / "src", ROOT / "contracts" / "build"]
    problems: list[str] = []
    files = 0
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.rho")):
            files += 1
            problems.extend(scan_file(path))
    if problems:
        for problem in problems:
            print(f"call-arity: {problem}", file=sys.stderr)
        return 1
    print(f"check-call-arity: {files} file(s), 0 mismatch(es)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
