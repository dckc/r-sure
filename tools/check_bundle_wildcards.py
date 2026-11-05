#!/usr/bin/env python3
"""Reject wildcard receive patterns in deploy terms.

The node's bundle normalizer rejects a published bundle whose body contains a wildcard
receive (`for (@(true, _) <- ch)`). A wildcard in a `match` case is fine; a wildcard in a
`for` pattern inside a per-object contract is not. Keep the source free of them rather than
discovering the class at deploy time.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "contracts" / "src" / "deploy"
# `for (` ... `<-` where a pattern component is exactly `_`.
FOR = re.compile(r"\bfor\s*\(([^)]*?)<-", re.S)


def main() -> int:
    problems: list[str] = []
    for path in sorted(DEPLOY.glob("*.rho")):
        text = path.read_text()
        for match in FOR.finditer(text):
            pattern = match.group(1)
            # A wildcard is a standalone `_`, not `_foo` or a name containing `_`.
            if re.search(r"(?<![A-Za-z0-9_])_(?![A-Za-z0-9_])", pattern):
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{path.name}:{line}: wildcard receive pattern {pattern.strip()!r}")
    for problem in problems:
        print(f"check-bundle-wildcards: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("check-bundle-wildcards: no wildcard receive patterns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
