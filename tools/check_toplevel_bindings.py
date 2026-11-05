#!/usr/bin/env python3
"""Every top-level contract name must be bound by the term's top-level `new`.

`contract Foo(...) = ...` listens on the name `Foo`; if `Foo` is not in the enclosing
`new`, the term has a free variable. The node's bundle normalizer then rejects it at deploy
time with "Bundle's content must not have free variables or wildcards", which `parse-check`
does not see because it only parses. This checker catches the class directly.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "contracts" / "src" / "deploy"
CONTRACT = re.compile(r"\bcontract\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
NEW = re.compile(r"\bnew\s+(.+?)\s+in\s*\{", re.S)


def strip_comments(text: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())


def top_level_new_names(text: str) -> set[str] | None:
    match = NEW.search(text)
    if not match:
        return None
    names = set()
    for item in match.group(1).split(","):
        item = item.strip()
        # `rl(`rho:registry:lookup`)` binds the bare name before the backtick.
        name = item.split("`", 1)[0].strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            names.add(name)
    return names


def top_level_contracts(text: str) -> list[tuple[str, int]]:
    """Contract definitions at brace depth 1 (directly inside the top-level `new`)."""
    # Remove comments first so braces in comments do not count.
    text = strip_comments(text)
    new_match = NEW.search(text)
    if not new_match:
        return []
    start = new_match.end()
    depth = 1
    found: list[tuple[str, int]] = []
    index = start
    while index < len(text):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                break
        elif depth == 1 and text.startswith("contract", index):
            before = text[index - 1] if index else " "
            after = text[index + 8] if index + 8 < len(text) else " "
            if not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_"):
                match = CONTRACT.match(text, index)
                if match:
                    line = text.count("\n", 0, index) + 1
                    found.append((match.group(1), line))
        index += 1
    return found


def main() -> int:
    problems: list[str] = []
    checked = 0
    for path in sorted(DEPLOY.glob("*.rho")):
        text = path.read_text()
        bound = top_level_new_names(text)
        if bound is None:
            problems.append(f"{path.name}: no top-level `new ... in`")
            continue
        checked += 1
        for name, line in top_level_contracts(text):
            if name not in bound:
                problems.append(
                    f"{path.name}:{line}: top-level contract {name} is not in the "
                    f"top-level new list"
                )
    for problem in problems:
        print(f"check-toplevel-bindings: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"check-toplevel-bindings: {checked} term(s), all top-level contracts bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
