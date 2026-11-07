# Coverage report

> **Status:** Generated from `deployments/suite-results.json`; not line coverage.

| Metric | Covered |
|---|---|
| Passed suites | 37/42 |
| Public arms asserted by passing suites | 126/151 (83.4%) |
| All registered arms asserted | 139/168 (82.7%) |
| Core flow arms asserted | 8/11 (72.7%) |
| Fixed findings with a passing regression suite asserting a linked arm | 20/25 |
| Invariants tracked | 13/13 |

A suite contributes only when it is `pass`, has at least one assertion and
emits `covered_arms` in its `RSURE_RESULT` trailer. Stubs and zero-assertion
suites contribute nothing. A fixed finding is counted only when a linking arm
appears in that asserted set, so the metric is zero before any suite runs.
