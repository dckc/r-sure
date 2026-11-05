#!/usr/bin/env python3
"""Run behavioural suites and record an honest pass / fail / not-run result.

Exit codes: 0 all pass, 1 any failure, 2 any not-run and no failure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "deployments" / "suite-results.json"
TIMEOUT = 900
TRAILER = re.compile(r"^RSURE_RESULT (\{.*\})$", re.M)

SUITES = {
    "root": "unit_root.py",
    "payments": "unit_payments.py",
    "syndicate": "unit_syndicate.py",
    "capital": "unit_capital.py",
    "broker": "unit_broker.py",
    "risk": "unit_risk.py",
    "slip": "unit_slip.py",
    "subscription": "unit_subscription.py",
    "binding": "unit_binding.py",
    "line": "unit_line.py",
    "policy": "unit_policy.py",
    "distribution": "unit_distribution.py",
    "premium": "unit_premium.py",
    "fund": "unit_fund.py",
    "books": "unit_books.py",
    "pause": "unit_pause.py",
    "pause_scope": "unit_pause_scope.py",
    "admin": "unit_admin.py",
    "admin_keys": "unit_admin_keys.py",
    "cell_liveness": "unit_cell_liveness.py",
    "factory_auth": "unit_factory_auth.py",
    "replay": "unit_replay.py",
    "expiry": "unit_expiry.py",
    "evidence": "unit_evidence.py",
    "oracle": "unit_oracle.py",
    "claim_lifecycle": "unit_claim_lifecycle.py",
    "claim_refusals": "unit_claim_refusals.py",
    "settlement": "unit_settlement.py",
    "shortfall": "unit_shortfall.py",
    "conservation": "unit_conservation.py",
    "behavior": "unit_behavior.py",
    "generality": "unit_generality.py",
    "share_reuse": "unit_share_reuse.py",
    "integration_rcash": "integration_rcash.py",
    "integration_rgen": "integration_rgen.py",
    "integration_rshare": "integration_rshare.py",
}
DEFAULT = list(SUITES)


def run(name: str) -> dict:
    script = ROOT / "harness" / SUITES[name]
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    started = time.time()
    if not script.is_file():
        print(f"--- {name}: not_run (missing {script.name}) ---")
        return {"suite": name, "script": SUITES[name], "status": "not_run",
                "returncode": 2, "seconds": 0, "output": "missing script",
                "started_at": started_at, "assertions": 0, "covered_arms": [],
                "env_reason": "missing suite script"}
    try:
        proc = subprocess.run([sys.executable, str(script)], cwd=ROOT, text=True,
                              capture_output=True, timeout=TIMEOUT)
        output = (proc.stdout or "") + (proc.stderr or "")
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or "") if isinstance(exc.stdout, str) else "") + \
                 ((exc.stderr or "") if isinstance(exc.stderr, str) else "")
        returncode = 1
        output += f"\ntimeout after {TIMEOUT}s"
    trailer = None
    match = TRAILER.search(output)
    if match:
        try:
            trailer = json.loads(match.group(1))
        except json.JSONDecodeError:
            trailer = None
    assertions = int(trailer.get("assertions", 0)) if trailer else 0
    covered = list(trailer.get("covered_arms", [])) if trailer else []
    env_reason = None
    if returncode == 2:
        reason = re.search(r"not_run:\s*(.+)", output)
        env_reason = reason.group(1).strip() if reason else "suite reported not_run"
    if returncode == 2:
        status = "not_run"
    elif returncode == 0 and trailer and assertions > 0 and trailer.get("failed", 0) == 0:
        status = "pass"
    else:
        status = "fail"
        if returncode == 0 and (not trailer or assertions == 0):
            env_reason = "zero assertions (missing RSURE_RESULT trailer or empty suite)"
    print(f"--- {name}: {status} ({returncode}) ---")
    print(output.rstrip())
    return {"suite": name, "script": SUITES[name], "status": status,
            "returncode": returncode, "seconds": round(time.time() - started, 3),
            "output": output[-4000:], "started_at": started_at,
            "assertions": assertions, "covered_arms": covered,
            "env_reason": env_reason}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="suite names; default: all implemented")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--keystores", action="store_true")
    args = ap.parse_args(argv)

    if args.list:
        for name, script in SUITES.items():
            print(f"{name:20} {script}")
        return 0

    names = list(SUITES) if args.all else (args.names or DEFAULT)
    unknown = [name for name in names if name not in SUITES]
    if unknown:
        print(f"run_suites: unknown suites {unknown}", file=sys.stderr)
        return 1

    results = [run(name) for name in names]
    payload = {
        "node": os.environ.get("RSURE_NODE", "http://localhost:40403"),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": results,
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"run_suites: wrote {RESULTS.relative_to(ROOT)}")

    if any(item["status"] == "fail" for item in results):
        return 1
    if any(item["status"] == "not_run" for item in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
