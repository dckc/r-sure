#!/usr/bin/env python3
"""Check that global pause is wired, narrow, fail-closed and recovery-safe.

The gate must be present in the new-risk arms, absent from claims/settlement/expiry/
refund/recovery arms, and the per-file `isPaused` helper must fail closed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "contracts" / "src" / "deploy"
TERMINAL = ("settle", "close", "expire", "cancel", "refund", "release")
CLAIMS = ("openclaim", "addevidence", "classify", "assess", "agree", "dispute", "cover")
CONTRACT = re.compile(r"^\s*contract\s+([A-Za-z_]\w*)\s*\(", re.M)

# Narrow pause: new risk creation and binding only.
GATED = {
    ("10_syndicate.rho", "SyndicateBook", "create"),
    ("10_syndicate.rho", "Syndicate", "quote"),
    ("10_syndicate.rho", "Syndicate", "openLine"),
    ("11_broker.rho", "Broker", "addSlip"),
    ("12_risk.rho", "RiskBook", "submit"),
    ("12_risk.rho", "Risk", "accept"),
    ("12_risk.rho", "Risk", "decline"),
    ("16_fund.rho", "SureFund", "contribute"),
}


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
                    signature = text[match.start():brace]
                    yield match.group(1), signature, text[brace:index + 1]
                    break


def arm_of(signature: str) -> str | None:
    match = re.search(r'@"([^"]+)"', signature)
    return match.group(1) if match else None


def main() -> int:
    problems: list[str] = []
    pause_written = False
    pause_read = False
    gated_seen: set[tuple[str, str, str]] = set()
    helper_seen = False

    for path in sorted(DEPLOY.glob("*.rho")):
        text = path.read_text()
        if re.search(r'"pauseAll"', text):
            pause_written = True
        for name, signature, body in bodies(text):
            arm = arm_of(signature)
            if name == "isPaused" and arm is None:
                helper_seen = True
                if "ret!(true)" not in body:
                    problems.append(f"{path.name}: isPaused helper is not fail-closed")
                if "isPaused" in body:
                    pause_read = True
            if arm is None:
                continue
            if "isPaused!" in body:
                pause_read = True
                gated_seen.add((path.name, name, arm))
                if any(word in arm.lower() for word in TERMINAL + CLAIMS):
                    problems.append(
                        f"{path.name}: {name}@\"{arm}\" consults isPaused; terminal/"
                        "claims/recovery arms must not be blocked by global pause")
            elif any(word in arm.lower() for word in TERMINAL + CLAIMS):
                continue

    if pause_written and not pause_read:
        problems.append("pauseAll is written but no arm consults isPaused")
    if not helper_seen:
        problems.append("no per-file isPaused helper found")
    for key in sorted(GATED):
        if key not in gated_seen:
            problems.append(f"gated arm missing pause check: {key[0]} {key[1]}@\"{key[2]}\"")

    if problems:
        for problem in problems:
            print(f"pause-scope: {problem}", file=sys.stderr)
        return 1
    print("pause-scope: pause is wired, narrow, fail-closed and recovery-safe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
