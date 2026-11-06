#!/usr/bin/env python3
"""Check the critical-path manifest against claims, Lean, flows, arms and suites.

The manifest `spec/critical-path.yaml` is the campaign gate for the 15 critical
primitives. A primitive may be `status: covered` only when:

  * its claims.yaml entry is `covered` with a substantive, axiom-audited `*_sound`
    theorem (plus a refusal and a reachability theorem);
  * its model file exists and every cited theorem resolves in spec/lean;
  * every arm has a `proved-model`/`proved-model-bounded` flow rule whose source
    contains the arm;
  * every arm exists in audit/registers/arms.yaml;
  * every suite maps to a harness suite and a tests register row;
  * every hazard id exists in audit/registers/hazards.yaml.

Exit codes: 0 ok, 1 defect, 2 missing input.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "spec" / "critical-path.yaml"
CLAIMS = ROOT / "spec" / "lean" / "claims.yaml"
FLOWS = ROOT / "spec" / "flows"
ARMS_REGISTER = ROOT / "audit" / "registers" / "arms.yaml"
TESTS_REGISTER = ROOT / "audit" / "registers" / "tests.yaml"
HAZARDS_REGISTER = ROOT / "audit" / "registers" / "hazards.yaml"
LEAN = ROOT / "spec" / "lean"
AUDIT = LEAN / "RSure" / "Audit.lean"

REQUIRED_IDS = [f"CP-{i:02d}" for i in range(1, 16)]
FLOW_STATUSES = {"proved-model", "proved-model-bounded"}
BAD_STATUSES = {"deferred", "partial", "tool", "owed", "open", "modeled", "assumption"}
ARM_RE = re.compile(r"^(?P<component>[A-Za-z0-9_]+)@\"(?P<arm>[^\"]+)\"$")


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing {path.relative_to(ROOT)}")
    return yaml.safe_load(path.read_text()) or {}


def lean_index() -> tuple[set[str], dict[str, str], set[str]]:
    """Return (fully-qualified theorem names, bodies, audited names)."""
    # Reuse the claim checker's namespace-aware declaration scanner.
    sys.path.insert(0, str(ROOT / "tools"))
    import check_claims as claims_tool  # noqa: E402

    names, bodies = claims_tool.lean_declarations()
    audited = claims_tool.audit_names()
    return names, bodies, audited


def body_is_weak(body: str) -> bool:
    sys.path.insert(0, str(ROOT / "tools"))
    import check_claims as claims_tool  # noqa: E402

    term = claims_tool.body_term(body)
    return bool(term and claims_tool.WEAK_BODY.match(term))


def flow_rules() -> dict[str, list[dict]]:
    by_arm: dict[str, list[dict]] = {}
    for path in sorted(FLOWS.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        for rule in doc.get("rules", []):
            rule = dict(rule)
            rule["_file"] = path.name
            by_arm.setdefault(rule.get("arm"), []).append(rule)
    return by_arm


def arm_register() -> set[str]:
    doc = load_yaml(ARMS_REGISTER)
    return {
        f'{row.get("component")}@"{row.get("arm")}"'
        for row in doc.get("arms", [])
    }


def suite_index() -> tuple[set[str], set[str]]:
    """Return (harness suite stems, tests register names/files)."""
    harness = {path.stem for path in (ROOT / "harness").glob("*.py")}
    doc = load_yaml(TESTS_REGISTER)
    names = {row.get("name") for row in doc.get("tests", [])}
    files = {Path(row.get("file", "")).stem for row in doc.get("tests", [])}
    return harness, names | files


def hazard_ids() -> set[str]:
    doc = load_yaml(HAZARDS_REGISTER)
    return {row.get("id") for row in doc.get("hazards", [])}


def check(manifest: dict, claims: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema") != "rsure.critical-path/v1":
        errors.append("critical-path: bad schema")
    rows = manifest.get("primitives") or []
    ids = [row.get("id") for row in rows]
    if sorted(ids) != sorted(REQUIRED_IDS):
        errors.append(
            "critical-path: primitive ids must be exactly CP-01..CP-15 "
            f"(got {ids})")
    claim_prims = claims.get("primitives") or {}
    if sorted(claim_prims) != sorted(REQUIRED_IDS):
        errors.append(
            "claims.yaml primitives must be exactly CP-01..CP-15 "
            f"(got {sorted(claim_prims)})")

    names, bodies, audited = lean_index()
    by_arm = flow_rules()
    registered_arms = arm_register()
    harness, test_names = suite_index()
    hazards = hazard_ids()
    claim_assumptions = set((claims.get("assumptions") or {}).keys())
    claim_invariants = set((claims.get("invariants") or {}).keys())
    global_theorems = {}
    for section in ("invariants", "primitives"):
        for entry in (claims.get(section) or {}).values():
            for theorem in entry.get("theorems") or []:
                global_theorems[theorem.get("name")] = theorem

    for row in rows:
        cp = row.get("id")
        label = f"{cp} {row.get('name')}"
        if row.get("status") != "covered":
            errors.append(f"{label}: manifest status {row.get('status')!r} is not covered")
        claim = claim_prims.get(cp)
        if not claim:
            errors.append(f"{label}: missing claims.yaml primitive")
            continue
        cstatus = claim.get("status")
        if cstatus != "covered":
            errors.append(f"{label}: claim status {cstatus!r} blocks the critical path")
        tie = claim.get("tie") or {}
        if tie.get("status") != "model-only":
            errors.append(f"{label}: claim tie.status must be model-only")
        if not claim.get("refinement_gap"):
            errors.append(f"{label}: claim has no refinement_gap")
        assumptions = claim.get("assumptions") or []
        if not assumptions:
            errors.append(f"{label}: claim has no boundary assumptions")
        for assumption in assumptions:
            if assumption not in claim_assumptions:
                errors.append(f"{label}: unknown assumption {assumption}")

        model = row.get("model")
        if not model or not (ROOT / model).is_file():
            errors.append(f"{label}: missing model {model}")
        elif not str(model).startswith("spec/lean/"):
            errors.append(f"{label}: model {model} is not under spec/lean")

        cited = list(row.get("theorems") or [])
        sound = row.get("soundness")
        if sound:
            cited.append(sound)
        claim_theorems = {t.get("name"): t for t in claim.get("theorems") or []}
        substantive = 0
        for name in cited:
            if name not in names:
                errors.append(f"{label}: theorem {name} does not resolve in spec/lean")
                continue
            entry = claim_theorems.get(name)
            if not entry:
                errors.append(f"{label}: {name} is not cited by the claim")
                continue
            if entry.get("strength") != "substantive":
                errors.append(f"{label}: {name} is not substantive")
            else:
                substantive += 1
            if body_is_weak(bodies.get(name, "")):
                errors.append(f"{label}: {name} has a hypothesis-restatement body")
            if name not in audited:
                errors.append(f"{label}: {name} is not in Audit.lean")
        if sound and not sound.rsplit(".", 1)[-1].endswith("_sound"):
            errors.append(f"{label}: soundness {sound} is not a *_sound theorem")
        if substantive == 0:
            errors.append(f"{label}: no substantive theorem")
        short_cited = [name.rsplit(".", 1)[-1] for name in cited]
        if not any("refuse" in name for name in short_cited):
            errors.append(f"{label}: no refusal theorem cited")
        if not any("reachable" in name for name in short_cited):
            errors.append(f"{label}: no reachability theorem cited")

        classes = row.get("required_classes") or []
        if not classes:
            errors.append(f"{label}: no required_classes")
        for inv in row.get("invariants") or []:
            if inv not in claim_invariants:
                errors.append(f"{label}: unknown invariant {inv}")

        sources = row.get("source") or []
        if not sources:
            errors.append(f"{label}: no source files")
        for source in sources:
            if not (ROOT / source).is_file():
                errors.append(f"{label}: missing source {source}")

        arms = row.get("arms") or []
        if not arms:
            errors.append(f"{label}: no arms")
        for arm in arms:
            match = ARM_RE.match(arm)
            if not match:
                errors.append(f"{label}: bad arm {arm!r}")
                continue
            if arm not in registered_arms:
                errors.append(f"{label}: arm {arm} is not in arms.yaml")
            rules = by_arm.get(arm, [])
            if not rules:
                errors.append(f"{label}: arm {arm} has no flow rule")
                continue
            good = [r for r in rules if r.get("lean_status") in FLOW_STATUSES]
            if not good:
                statuses = {r.get("lean_status") for r in rules}
                errors.append(
                    f"{label}: arm {arm} has no proved-model flow rule (statuses {statuses})")
            for rule in good:
                target = rule.get("lean")
                short_names = {name.rsplit(".", 1)[-1] for name in names}
                if not target or (target not in names
                                  and target.rsplit(".", 1)[-1] not in short_names):
                    errors.append(
                        f"{label}: flow {rule.get('id')} target {target} does not resolve")
                    continue
                target_entry = global_theorems.get(target)
                if not target_entry:
                    errors.append(
                        f"{label}: flow {rule.get('id')} target {target} is not a claim theorem")
                else:
                    if target_entry.get("strength") != "substantive":
                        errors.append(
                            f"{label}: flow {rule.get('id')} target {target} is not substantive")
                    if target not in audited:
                        errors.append(
                            f"{label}: flow {rule.get('id')} target {target} is unaudited")
                source = ROOT / (rule.get("source") or "")
                if not source.is_file():
                    errors.append(f"{label}: flow {rule.get('id')} source missing")
                elif f'contract {match.group("component")}(@"{match.group("arm")}"' \
                        not in source.read_text():
                    errors.append(
                        f"{label}: flow {rule.get('id')} arm {arm} not in {source.name}")

        suite = row.get("suite") or []
        if not suite:
            errors.append(f"{label}: no suite mapping")
        for name in suite:
            if name not in harness:
                errors.append(f"{label}: suite {name} has no harness file")
            if name not in test_names:
                errors.append(f"{label}: suite {name} has no tests register row")

        hz = row.get("hazards") or []
        if not hz:
            errors.append(f"{label}: no hazard mapping")
        for hazard in hz:
            if hazard not in hazards:
                errors.append(f"{label}: unknown hazard {hazard}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail on any defect")
    args = parser.parse_args(argv)
    manifest = load_yaml(MANIFEST)
    claims = load_yaml(CLAIMS)
    errors = check(manifest, claims)
    for error in errors:
        print(f"check-critical-path: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"check-critical-path: {len(manifest.get('primitives') or [])} critical "
          "primitives covered, arms/flows/suites/hazards joined")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
