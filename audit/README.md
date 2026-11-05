# r-sure audit and HAZOP

> **Status:** Internal desk and tabletop review, 2026-11-05. This is not an independent audit
> and does not certify the contracts, r-cash, r-gen or any deployment. Dynamic evidence is
> `not_run` until the P0 instance-bundle defect is fixed.

This directory is the working audit record. The registers are the editable source of truth;
the book chapters summarise them.

## Start here

| Artifact | Purpose |
|---|---|
| [charter.md](charter.md) | scope, roles and evidence standard |
| [method.md](method.md) | desk, concurrency, composition and HAZOP method |
| [report.md](report.md) | verdict, counts, P0/P1 status and residual risk |
| [concurrency/README.md](concurrency/README.md) | per-component concurrency review method |
| [concurrency/components.yaml](concurrency/components.yaml) | one row per component (30) |
| [composition/interfaces.yaml](composition/interfaces.yaml) | one row per interface (42) |
| [hazop/nodes.yaml](hazop/nodes.yaml) | 15 nodes, guide words and parameters |
| [hazop/tabletop-2026-11-05.md](hazop/tabletop-2026-11-05.md) | internal tabletop record |
| [registers/findings.yaml](registers/findings.yaml) | 21 findings |
| [registers/hazards.yaml](registers/hazards.yaml) | 27 hazards |
| [registers/improvements.yaml](registers/improvements.yaml) | 21 fixes/deferred items |
| [registers/tests.yaml](registers/tests.yaml) | 36 suites, all `not_run` |
| [registers/theorems.yaml](registers/theorems.yaml) | 106 Lean component-model theorems |
| [traceability/matrix.md](traceability/matrix.md) | generated arm/hazard/finding/test matrix |

## What to read for the verdict

1. `report.md` — the P0 bundle defect is open; install is blocked.
2. `findings.yaml` — F-001 (take-await-take) is fixed; F-002 (bundles) is open.
3. `concurrency/reviews/` — one review per component; no component is un-reviewed.
4. `hazop/tabletop-2026-11-05.md` — decisions and the internal-only limitation.

## Reproduce the static evidence

```sh
make audit-check
python3 tools/check_take_repost.py
python3 tools/check_bundle_closedness.py
python3 tools/check_reply_shapes.py
python3 tools/check_pause_scope.py
make unit-all
```

`make unit-all` is expected to report `not_run` until the devnet install clears F-002.
