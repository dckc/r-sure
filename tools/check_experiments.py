#!/usr/bin/env python3
"""Validate the RCA experiment register.

An experiment is only evidence if it names a runnable method, an artifact that exists, a
result, and the hypothesis it tested. The checker fails on dangling RCA/hypothesis links,
missing artifacts, an unexecuted status pretending to be complete, and an artifact that
is not in an evidence v2 manifest.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTERS = ROOT / "audit" / "registers"
EVIDENCE = ROOT / "audit" / "evidence"
SCHEMA = "rsure.experiments/v1"
REQUIRED = ("id", "rca", "question", "method", "command", "artifact", "result",
            "observed", "status", "tests_hypotheses", "conclusion")
RESULTS = {"pass", "fail", "inconclusive", "blocked"}
STATUSES = {"planned", "running", "completed", "abandoned"}
CONCLUSIONS = {"supports", "rejects", "inconclusive", "partial"}


def resolve(path_text: str) -> Path:
    candidate = Path(path_text)
    if candidate.is_absolute():
        return candidate
    direct = ROOT / candidate
    if direct.exists():
        return direct
    # Locally the node is a sibling checkout; CI checks it out inside the workspace.
    parts = candidate.parts
    if len(parts) >= 2 and parts[0] == ".." and parts[1] == "RNodeRust":
        inside = ROOT.joinpath("RNodeRust", *parts[2:])
        if inside.exists():
            return inside
    return direct


def manifest_artifacts() -> set[Path]:
    paths: set[Path] = set()
    for manifest in EVIDENCE.glob("*/manifest.json"):
        doc = json.loads(manifest.read_text())
        for artifact in doc.get("artifacts", []):
            rel = artifact.get("path")
            if not rel:
                continue
            local = manifest.parent / rel
            paths.add(local.resolve() if local.exists() else (ROOT / rel).resolve())
    return paths


def main() -> int:
    path = REGISTERS / "experiments.yaml"
    if not path.is_file():
        print(f"check-experiments: missing {path}", file=sys.stderr)
        return 1
    doc = yaml.safe_load(path.read_text())
    problems: list[str] = []
    if doc.get("schema") != SCHEMA:
        problems.append(f"schema {doc.get('schema')!r} is not {SCHEMA}")

    rca_doc = yaml.safe_load((REGISTERS / "rca.yaml").read_text())
    rcas = {record.get("id"): record for record in rca_doc.get("records", [])}
    hypotheses = {
        hypothesis.get("id")
        for record in rcas.values()
        for hypothesis in record.get("hypotheses", [])
    }

    experiments = doc.get("experiments", [])
    if not experiments:
        problems.append("no experiments")
    ids: set[str] = set()
    covered: set[str] = set()
    in_manifest = manifest_artifacts()

    for experiment in experiments:
        label = experiment.get("id") or "<no id>"
        for field in REQUIRED:
            if field not in experiment:
                problems.append(f"{label}: missing {field}")
        ident = experiment.get("id")
        if ident in ids:
            problems.append(f"{label}: duplicate id")
        ids.add(ident)

        rca_id = experiment.get("rca")
        if rca_id not in rcas:
            problems.append(f"{label}: dangling RCA {rca_id!r}")
        else:
            covered.add(rca_id)

        if experiment.get("result") not in RESULTS:
            problems.append(f"{label}: bad result {experiment.get('result')!r}")
        if experiment.get("status") not in STATUSES:
            problems.append(f"{label}: bad status {experiment.get('status')!r}")
        if experiment.get("conclusion") not in CONCLUSIONS:
            problems.append(f"{label}: bad conclusion {experiment.get('conclusion')!r}")
        if experiment.get("status") == "planned" and experiment.get("result") == "pass":
            problems.append(f"{label}: planned experiment cannot have a pass result")
        for field in ("question", "method", "command", "observed"):
            if not str(experiment.get(field, "")).strip():
                problems.append(f"{label}: empty {field}")

        hypotheses_tested = experiment.get("tests_hypotheses") or []
        if not hypotheses_tested:
            problems.append(f"{label}: no hypotheses tested")
        for hypothesis in hypotheses_tested:
            if hypothesis not in hypotheses:
                problems.append(f"{label}: dangling hypothesis {hypothesis}")
            elif rca_id in rcas and hypothesis not in {
                item.get("id") for item in rcas[rca_id].get("hypotheses", [])
            }:
                problems.append(f"{label}: hypothesis {hypothesis} is not in {rca_id}")

        artifact = experiment.get("artifact")
        if artifact:
            target = resolve(str(artifact))
            if not target.is_file():
                problems.append(f"{label}: artifact does not exist: {artifact}")
            elif str(artifact).startswith("audit/evidence") and target.resolve() not in in_manifest:
                problems.append(f"{label}: evidence artifact is not in a v2 manifest: {artifact}")
        for extra in experiment.get("supporting_artifacts", []) or []:
            if not resolve(str(extra)).is_file():
                problems.append(f"{label}: supporting artifact does not exist: {extra}")

    for rca_id, record in rcas.items():
        declared = set(record.get("experiments", []) or [])
        actual = {
            experiment.get("id")
            for experiment in experiments
            if experiment.get("rca") == rca_id
        }
        for missing in sorted(declared - actual):
            problems.append(f"{rca_id}: experiment {missing} is declared but missing")
        for extra in sorted(actual - declared):
            problems.append(f"{rca_id}: experiment {extra} is not declared")

    print(f"check-experiments: {len(experiments)} experiments across {len(covered)} RCA(s)")
    for problem in problems:
        print(f"check-experiments: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
