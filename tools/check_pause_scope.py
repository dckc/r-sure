#!/usr/bin/env python3
"""Check that global pause is wired and does not block terminal/financial recovery arms."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "contracts" / "src" / "deploy"
TERMINAL = ("settle", "close", "expire", "cancel", "refund", "release")
CONTRACT = re.compile(r"^\s*contract\s+([A-Za-z_]\w*)\s*\(\s*@?\"([^\"]+)\"", re.M)


def bodies(text: str):
    for match in CONTRACT.finditer(text):
        brace = text.find("{", match.end())
        if brace < 0:
            continue
        depth = 0
        for index in range(brace, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    yield match.group(1), match.group(2), text[brace:index + 1]
                    break


def main() -> int:
    problems: list[str] = []
    pause_written = False
    pause_read = False
    for path in sorted(DEPLOY.glob("*.rho")):
        text = path.read_text()
        if re.search(r'"pauseAll"', text):
            pause_written = True
        for name, arm, body in bodies(text):
            if re.search(r"isPaused", body):
                pause_read = True
                if any(word in arm.lower() for word in TERMINAL):
                    problems.append(
                        f"{path.name}: {name}@\"{arm}\" consults isPaused; terminal/"
                        "recovery arms must not be blocked by global pause")
    if pause_written and not pause_read:
        problems.append("pauseAll is written but no arm consults isPaused")
    if problems:
        for problem in problems:
            print(f"pause-scope: {problem}", file=sys.stderr)
        return 1
    print("pause-scope: pause is wired and excluded from terminal recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
