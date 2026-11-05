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

## Concurrency row

`component`, `file`, `kind`, `state_cells`, `cross_cell_writers`, `writers`, `readers`,
`awaits_while_holding_state`, `value_moves`, `bundle_publication`, `replay_guard`, `hazards`,
`verdict`, `review`.

## Interface row

`id`, `caller`, `callee`, `arm`, `call_site`, `request`, `success_reply`, `refusal_reply`,
`awaits`, `state_held`, `atomicity`, `capabilities`, `hazards`, `verdict`.
