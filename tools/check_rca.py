#!/usr/bin/env python3
"""Validate the RCA register and its links.

The checker is the executable RCA schema: an incident needs a fault tree with evidence at
every leaf, five whys, at least one hypothesis, experiments, a root cause, an escape
analysis, corrective actions, a verification table and residual risk. New P0/P1 findings
and new install hazards must be linked to a record.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTERS = ROOT / "audit" / "registers"
SCHEMA = "rsure.rca/v1"
REQUIRED = ("id", "title", "date", "owner", "severity", "status", "template", "nodes",
            "findings", "hazards", "experiments", "incident", "fault_tree", "five_whys",
            "hypotheses", "root_cause", "escape_analysis", "corrective_actions",
            "verification", "residual_risk", "evidence")
SEVERITIES = {"P0", "P1", "P2", "P3"}
STATUSES = {"open", "closed", "monitoring"}
HYPOTHESIS_STATUSES = {"supported", "rejected", "partial", "inconclusive"}
ACTION_STATUSES = {"done", "open", "monitoring"}
VERIFICATION_RESULTS = {"pass", "fail", "not_run", "partial", "implemented-not-executed",
                        "blocked"}
GATES = {"AND", "OR", "LEAF"}
TEMPLATE_HEADINGS = ("## Identity", "## Incident", "## Fault tree", "## Five whys",
                     "## Hypotheses", "## Experiments", "## Root cause",
                     "## Escape analysis", "## Corrective actions", "## Verification",
                     "## Residual risk")
NEW_FINDING = re.compile(r"^F-(\d+)$")
NEW_HAZARD = re.compile(r"^HZ-(\d+)$")


def load(name: str) -> dict:
    return yaml.safe_load((REGISTERS / name).read_text())


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    direct = ROOT / path
    if direct.exists():
        return direct
    # Locally the node is a sibling checkout; CI checks it out inside the workspace.
    parts = path.parts
    if len(parts) >= 2 and parts[0] == ".." and parts[1] == "RNodeRust":
        inside = ROOT.joinpath("RNodeRust", *parts[2:])
        if inside.exists():
            return inside
    return direct


def ids_of(items: list[dict]) -> set[str]:
    return {item.get("id") for item in items}


def check_tree(node: dict, label: str, problems: list[str]) -> None:
    event = node.get("event") or node.get("top_event")
    gate = node.get("gate")
    if not str(event or "").strip():
        problems.append(f"{label}: fault-tree node without event")
    if gate not in GATES:
        problems.append(f"{label}: bad fault-tree gate {gate!r}")
        return
    evidence = node.get("evidence") or []
    if not evidence:
        problems.append(f"{label}: fault-tree node {event!r} has no evidence")
    for ref in evidence:
        if not resolve(str(ref)).exists():
            problems.append(f"{label}: fault-tree evidence does not exist: {ref}")
    children = node.get("children") or []
    if gate in {"AND", "OR"} and not children:
        problems.append(f"{label}: {gate} node {event!r} has no children")
    if gate == "LEAF" and children:
        problems.append(f"{label}: LEAF node {event!r} has children")
    for child in children:
        check_tree(child, label, problems)


def main() -> int:
    path = REGISTERS / "rca.yaml"
    if not path.is_file():
        print(f"check-rca: missing {path}", file=sys.stderr)
        return 1
    doc = yaml.safe_load(path.read_text())
    problems: list[str] = []
    if doc.get("schema") != SCHEMA:
        problems.append(f"schema {doc.get('schema')!r} is not {SCHEMA}")

    finding_rows = load("findings.yaml").get("findings", [])
    findings = ids_of(finding_rows)
    hazard_rows = load("hazards.yaml").get("hazards", [])
    hazards = ids_of(hazard_rows)
    # The RCA-link rule is for install/test-campaign hazards (N16-N19), not for
    # domain hazards such as risk measurement.
    install_hazards = {
        row.get("id") for row in hazard_rows
        if row.get("node") in {"N16", "N17", "N18", "N19"}
    }
    improvements = ids_of(load("improvements.yaml").get("improvements", []))
    experiments = ids_of(load("experiments.yaml").get("experiments", []))
    nodes = ids_of(yaml.safe_load((ROOT / "audit" / "hazop" / "nodes.yaml").read_text())
                   .get("nodes", []))

    records = doc.get("records", [])
    if not records:
        problems.append("no RCA records")
    record_ids: set[str] = set()
    linked_findings: set[str] = set()
    linked_hazards: set[str] = set()

    for record in records:
        label = record.get("id") or "<no id>"
        for field in REQUIRED:
            if field not in record:
                problems.append(f"{label}: missing {field}")
        if record.get("id") in record_ids:
            problems.append(f"{label}: duplicate id")
        record_ids.add(record.get("id"))
        if record.get("severity") not in SEVERITIES:
            problems.append(f"{label}: bad severity {record.get('severity')!r}")
        if record.get("status") not in STATUSES:
            problems.append(f"{label}: bad status {record.get('status')!r}")
        if not str(record.get("root_cause", "")).strip():
            problems.append(f"{label}: empty root_cause")

        template = resolve(str(record.get("template", "")))
        if not template.is_file():
            problems.append(f"{label}: missing template {record.get('template')!r}")
        else:
            text = template.read_text()
            for heading in TEMPLATE_HEADINGS:
                if heading not in text:
                    problems.append(f"{label}: template missing heading {heading!r}")

        for node in record.get("nodes") or []:
            if node not in nodes:
                problems.append(f"{label}: dangling node {node}")
        for finding in record.get("findings") or []:
            if finding not in findings:
                problems.append(f"{label}: dangling finding {finding}")
            linked_findings.add(finding)
        for hazard in record.get("hazards") or []:
            if hazard not in hazards:
                problems.append(f"{label}: dangling hazard {hazard}")
            linked_hazards.add(hazard)
        for experiment in record.get("experiments") or []:
            if experiment not in experiments:
                problems.append(f"{label}: dangling experiment {experiment}")

        tree = record.get("fault_tree") or {}
        if not str(tree.get("top_event", "")).strip():
            problems.append(f"{label}: fault_tree without top_event")
        check_tree(tree, label, problems)

        whys = record.get("five_whys") or []
        if len(whys) < 5:
            problems.append(f"{label}: fewer than five whys ({len(whys)})")
        for index, why in enumerate(whys, start=1):
            if not str(why.get("question", "")).strip():
                problems.append(f"{label}: why {index} has no question")
            if not str(why.get("answer", "")).strip():
                problems.append(f"{label}: why {index} has no answer")

        hypotheses = record.get("hypotheses") or []
        if not hypotheses:
            problems.append(f"{label}: no hypotheses")
        hypothesis_ids: set[str] = set()
        for hypothesis in hypotheses:
            hid = hypothesis.get("id")
            if not hid or hid in hypothesis_ids:
                problems.append(f"{label}: bad or duplicate hypothesis {hid!r}")
            hypothesis_ids.add(hid)
            if not str(hypothesis.get("statement", "")).strip():
                problems.append(f"{label}: hypothesis {hid} has no statement")
            if hypothesis.get("status") not in HYPOTHESIS_STATUSES:
                problems.append(f"{label}: hypothesis {hid} bad status "
                                f"{hypothesis.get('status')!r}")

        escape = record.get("escape_analysis") or []
        if not escape:
            problems.append(f"{label}: empty escape_analysis")
        if not all(isinstance(item, str) and item.strip() for item in escape):
            problems.append(f"{label}: escape_analysis must be non-empty strings")

        actions = record.get("corrective_actions") or []
        if not actions:
            problems.append(f"{label}: no corrective_actions")
        action_ids: set[str] = set()
        for action in actions:
            aid = action.get("id")
            if not aid or aid in action_ids:
                problems.append(f"{label}: bad or duplicate action {aid!r}")
            action_ids.add(aid)
            for field in ("action", "owner"):
                if not str(action.get(field, "")).strip():
                    problems.append(f"{label}: action {aid} has no {field}")
            if action.get("status") not in ACTION_STATUSES:
                problems.append(f"{label}: action {aid} bad status "
                                f"{action.get('status')!r}")
            for finding in action.get("findings", []) or []:
                if finding not in findings:
                    problems.append(f"{label}: action {aid} dangling finding {finding}")
            for improvement in action.get("improvements", []) or []:
                if improvement not in improvements:
                    problems.append(f"{label}: action {aid} dangling improvement "
                                    f"{improvement}")

        verification = record.get("verification") or {}
        if not verification:
            problems.append(f"{label}: empty verification")
        for key, check in verification.items():
            if check.get("result") not in VERIFICATION_RESULTS:
                problems.append(f"{label}: verification {key} bad result "
                                f"{check.get('result')!r}")
            refs = check.get("evidence") or []
            if not refs:
                problems.append(f"{label}: verification {key} has no evidence")
            for ref in refs:
                if not resolve(str(ref)).is_file():
                    problems.append(f"{label}: verification {key} evidence does not "
                                    f"exist: {ref}")

        residual = record.get("residual_risk") or []
        if not residual:
            problems.append(f"{label}: empty residual_risk")
        if not all(isinstance(item, str) and item.strip() for item in residual):
            problems.append(f"{label}: residual_risk must be non-empty strings")

        for ref in record.get("evidence") or []:
            if not resolve(str(ref)).exists():
                problems.append(f"{label}: evidence does not exist: {ref}")

    for row in finding_rows:
        finding = row.get("id")
        match = NEW_FINDING.match(str(finding))
        if not match or int(match.group(1)) < 22:
            continue
        # Code-hygiene findings (P2/P3) do not need an incident record; P0/P1 do.
        if row.get("severity") not in {"P0", "P1"}:
            continue
        record = next((r for r in records if finding in (r.get("findings") or [])), None)
        if not record:
            problems.append(f"{finding}: new finding is not linked to an RCA record")
    for hazard in hazards:
        if hazard not in install_hazards:
            continue
        match = NEW_HAZARD.match(str(hazard))
        if not match or int(match.group(1)) < 28:
            continue
        record = next((r for r in records if hazard in (r.get("hazards") or [])), None)
        if not record:
            problems.append(f"{hazard}: new install hazard is not linked to an RCA record")

    print(f"check-rca: {len(records)} records, {len(linked_findings)} findings, "
          f"{len(linked_hazards)} hazards, {len(experiments)} experiments")
    for problem in problems:
        print(f"check-rca: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
