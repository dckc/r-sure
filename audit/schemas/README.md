# Register schemas

The executable schemas are in `tools/check_audit.py` and the coverage gates. The fields are:

## Finding

`id`, `title`, `severity` (P0–P3), `class`, `status` (`confirmed|suspected|disputed|fixed|
deferred|accepted`), `confidence`, `components`, `arms`, `hazards`, `invariants`,
`evidence_level` (E0–E4), `evidence` (`[{kind, ref}]`), `description`, `preconditions`,
`impact`, `proposed_fix` (an improvement ID), `reviewer`, `verified_at`.

## Hazard

`id`, `node`, `guide_word`, `parameter`, `deviation`, `causes`, `consequences`, `severity`,
`likelihood`, `risk`, `controls`, `findings`, `tests`, `disposition`
(`avoid|mitigate|transfer|accept|open`), `owner`, `evidence`.

## Improvement

`id`, `priority`, `findings`, `hazards`, `change`, `type`, `breaking`, `migration`,
`compatibility_window`, `tests`, `rollout_stage`, `rollback`, `status`.

## Test

`id`, `name`, `file`, `status` (`planned|implemented|passing|failing|not_run`), `focus`.
`implemented` means source plus static/parser gates, never behavioural verification.

## Evidence manifest (`rsure.evidence/v2`)

`schema` (exactly `rsure.evidence/v2`), `id` (must match the directory name), `date`,
`kind`, `commit`, `scope` (`audit: internal|independent`, `production: false`, `dynamic`),
`artifacts` (`path`, `role`, `sha256`, `bytes`, `description`), `commands`, `results`,
`reasons` (required for any `not_run`, `partial`, `blocked` or `fail` result),
`limitations`. The checker verifies every artifact hash and byte size, rejects a missing
limitation, and refuses a production claim.

## RCA record (`rsure.rca/v1`)

`id`, `title`, `date`, `owner`, `severity`, `status` (`open|closed|monitoring`), `template`,
`nodes`, `findings`, `hazards`, `experiments`, `incident`, `fault_tree` (`top_event`,
`gate`, `evidence`, `children` recursively), `five_whys` (at least five
`{question, answer}` rows), `hypotheses` (`id`, `statement`, `status`), `root_cause`,
`escape_analysis`, `corrective_actions`, `verification`, `residual_risk`, `evidence`.
Every new P0/P1 finding (F-022+) and new install hazard (HZ-028+) must link to a record.

## Experiment (`rsure.experiments/v1`)

`id`, `rca`, `question`, `method`, `command`, `artifact`, `result`
(`pass|fail|inconclusive|blocked`), `observed`, `status`
(`planned|running|completed|abandoned`), `tests_hypotheses`, `conclusion`
(`supports|rejects|inconclusive|partial`). Every artifact exists; artifacts under
`audit/evidence/` must appear in a v2 manifest.

## Concurrency row

`component`, `file`, `kind`, `state_cells`, `cross_cell_writers`, `writers`, `readers`,
`awaits_while_holding_state`, `value_moves`, `bundle_publication`, `replay_guard`, `hazards`,
`verdict`, `review`.

## Interface row

`id`, `caller`, `callee`, `arm`, `call_site`, `request`, `success_reply`, `refusal_reply`,
`awaits`, `state_held`, `atomicity`, `capabilities`, `hazards`, `verdict`.
