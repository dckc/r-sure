#!/usr/bin/env python3
"""Static guards for F-020 (aggregate cap) and F-021 (terminal claim states)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "contracts" / "src" / "deploy"
CONTRACT = re.compile(r"^\s*contract\s+([A-Za-z_]\w*)\s*\(", re.M)


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
                    yield match.group(1), text[match.start():brace], text[brace:index + 1]
                    break


def arm_of(signature: str) -> str | None:
    match = re.search(r'@"([^"]+)"', signature)
    return match.group(1) if match else None


def require(path: Path, contract: str, arm: str | None, needles: list[str],
            problems: list[str]) -> None:
    text = path.read_text()
    matches = [body for name, sig, body in bodies(text)
               if name == contract and (arm is None or arm_of(sig) == arm)]
    if not matches:
        problems.append(f"{path.name}: missing {contract}@{arm}")
        return
    if not any(all(needle in body for needle in needles) for body in matches):
        problems.append(
            f"{path.name}: {contract}@{arm} missing guard fragment(s) {needles}")


def main() -> int:
    problems: list[str] = []
    require(DEPLOY / "04_math.rho", "SureMath", "payable",
            ["perClaimLimit < aggregateRemaining", "pay > aggregateRemaining",
             '"aggregate"'], problems)
    require(DEPLOY / "17_policy.rho", "Policy", "settleClaim",
            ["policyState!(s) | ret2!(pay)"], problems)
    for arm in ("addEvidence", "classify", "assess", "agree", "dispute"):
        require(DEPLOY / "18_claim.rho", "Claim", arm,
                ['"settled"', '"denied"', '"closed"'], problems)
    require(DEPLOY / "18_claim.rho", "claimApplyDecision", None,
            ['"settled"', '"denied"', '"closed"'], problems)

    if problems:
        for problem in problems:
            print(f"invariant-guards: {problem}", file=sys.stderr)
        return 1
    print("invariant-guards: payable minimum, aggregate propagation and terminal "
          "claim guards present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
