#!/usr/bin/env python3
"""Run behavioural suites and record an honest pass / fail / not-run result.

Exit codes: 0 all pass, 1 any failure, 2 any not-run and no failure.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "deployments" / "suite-results.json"

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
    if not script.is_file():
        print(f"--- {name}: not_run (missing {script.name}) ---")
        return {"suite": name, "script": SUITES[name], "status": "not_run",
                "returncode": 2, "seconds": 0, "output": "missing script"}
    started = time.time()
    proc = subprocess.run([sys.executable, str(script)], cwd=ROOT, text=True,
                          capture_output=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    status = "pass" if proc.returncode == 0 else "not_run" if proc.returncode == 2 else "fail"
    print(f"--- {name}: {status} ({proc.returncode}) ---")
    print(output.rstrip())
    return {"suite": name, "script": SUITES[name], "status": status,
            "returncode": proc.returncode, "seconds": round(time.time() - started, 3),
            "output": output[-4000:]}


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
