import RSure.Basic
import RSure.Model.Math
import RSure.Model.Terms
import RSure.Model.Grant
import RSure.Model.Syndicate
import RSure.Model.Line
import RSure.Model.Slip
import RSure.Model.Distribution
import RSure.Model.Fund
import RSure.Model.Policy
import RSure.Model.Claim
import RSure.Model.Oracle
import RSure.Model.Books
import RSure.Model.System
import RSure.Linear.Cell
import RSure.Linear.Protocol

-- Axiom audit: every source theorem must appear here.
#print axioms RSure.share_zero
#print axioms RSure.share_bps_zero
#print axioms RSure.div_add_div_le
#print axioms RSure.share_add_le
#print axioms RSure.share_le_self
#print axioms RSure.share_sum_le
#print axioms RSure.share_sum_le_self
#print axioms RSure.sumNat_append
#print axioms RSure.Model.Math.math_premiumSplit_le
#print axioms RSure.Model.Math.math_premiumSplit_conserves
#print axioms RSure.Model.Math.math_premiumSplit_commission_le
#print axioms RSure.Model.Math.math_premiumSplit_levy_le
#print axioms RSure.Model.Math.math_payable_le_agreed
#print axioms RSure.Model.Math.math_payable_le_perClaim
#print axioms RSure.Model.Math.math_payable_le_aggregate
#print axioms RSure.Model.Math.math_payable_zero_of_le_deductible
#print axioms RSure.Model.Math.math_allocAux_sums
#print axioms RSure.Model.Math.math_alloc_sums
#print axioms RSure.Model.Math.math_lineExposures_sums
#print axioms RSure.Model.Terms.terms_validate_sound
#print axioms RSure.Model.Terms.terms_validate_asset
#print axioms RSure.Model.Grant.grant_consume_moves
#print axioms RSure.Model.Grant.grant_consume_once
#print axioms RSure.Model.Syndicate.synd_quote_WF
#print axioms RSure.Model.Syndicate.synd_quote_reserves
#print axioms RSure.Model.Syndicate.synd_quote_requires_capacity
#print axioms RSure.Model.Syndicate.synd_openLine_WF
#print axioms RSure.Model.Syndicate.synd_openLine_moves
#print axioms RSure.Model.Syndicate.synd_release_restores
#print axioms RSure.Model.Syndicate.synd_payLoss_preserves_free
#print axioms RSure.Model.Syndicate.synd_written_le_capital
#print axioms RSure.Model.Syndicate.synd_capacity_invariant
#print axioms RSure.Model.Line.line_pay_fields
#print axioms RSure.Model.Line.line_pay_bounded
#print axioms RSure.Model.Line.line_pay_once
#print axioms RSure.Model.Line.line_pay_once_per_claim
#print axioms RSure.Model.Line.line_release_restores
#print axioms RSure.Model.Line.line_invariant
#print axioms RSure.Model.Slip.slip_bind_requires_subscription
#print axioms RSure.Model.Slip.slip_share_sum_bps
#print axioms RSure.Model.Slip.slip_bind_moves
#print axioms RSure.Model.Slip.slip_expire_refund
#print axioms RSure.Model.Distribution.distribution_planAux_sums
#print axioms RSure.Model.Distribution.distribution_plan_sums
#print axioms RSure.Model.Distribution.distribution_plan_single
#print axioms RSure.Model.Distribution.distribution_run_once
#print axioms RSure.Model.Distribution.distribution_run_preserves_plan
#print axioms RSure.Model.Distribution.distribution_run_sums
#print axioms RSure.Model.Fund.fund_cover_bounds
#print axioms RSure.Model.Fund.fund_cover_records
#print axioms RSure.Model.Fund.fund_cover_le_balance
#print axioms RSure.Model.Fund.fund_cover_le_cap
#print axioms RSure.Model.Fund.fund_conserves
#print axioms RSure.Model.Fund.fund_cover_once
#print axioms RSure.Model.Policy.policy_distribute_conserves
#print axioms RSure.Model.Policy.policy_distribute_once
#print axioms RSure.Model.Policy.policy_settle_fields
#print axioms RSure.Model.Policy.policy_settle_once
#print axioms RSure.Model.Policy.policy_settle_remaining
#print axioms RSure.Model.Policy.policy_settle_guard
#print axioms RSure.Model.Policy.policy_settle_aggregate
#print axioms RSure.Model.Policy.policy_settle_conserves
#print axioms RSure.Model.Policy.policy_terminal
#print axioms RSure.Model.Policy.policy_payable_le_agreed
#print axioms RSure.Model.Policy.policy_payable_le_perClaim
#print axioms RSure.Model.Claim.claim_agree_standard_lead
#print axioms RSure.Model.Claim.claim_agree_complex_quorum
#print axioms RSure.Model.Claim.claim_agree_complex_requires_lead
#print axioms RSure.Model.Claim.claim_settle_once
#print axioms RSure.Model.Claim.claim_paid_le_agreed
#print axioms RSure.Model.Claim.claim_terminal_sticky
#print axioms RSure.Model.Claim.claim_apply_case_bound
#print axioms RSure.Model.Claim.claim_apply_uphold
#print axioms RSure.Model.Claim.claim_apply_partial
#print axioms RSure.Model.Claim.claim_apply_revoke
#print axioms RSure.Model.Claim.claim_agree_terminal
#print axioms RSure.Model.Claim.claim_applyDecision_terminal
#print axioms RSure.Model.Oracle.oracle_decide_requires_credential
#print axioms RSure.Model.Oracle.oracle_execute_once
#print axioms RSure.Model.Oracle.oracle_execute_subject_bound
#print axioms RSure.Model.Oracle.oracle_applied_matches
#print axioms RSure.Model.Oracle.oracle_apply_once
#print axioms RSure.Model.Oracle.oracle_close_requires_finished
#print axioms RSure.Model.Books.book_register_absent
#print axioms RSure.Model.Books.book_lookup_sound
#print axioms RSure.Model.Books.book_register_unique
#print axioms RSure.Model.Books.book_lookup_preserved
#print axioms RSure.Model.System.system_step_atomic
#print axioms RSure.Model.System.system_step_refuses
#print axioms RSure.Model.System.system_settlement_conserves
#print axioms RSure.Model.System.system_settlement_plan
#print axioms RSure.Store.set_same
#print axioms RSure.Store.set_other
#print axioms RSure.peek_then_put_rejected
#print axioms RSure.put_without_take_rejected
#print axioms RSure.take_without_put_not_wf
#print axioms RSure.nested_call_rejected
#print axioms RSure.take_put_commit
#print axioms RSure.wf_quiescent
#print axioms RSure.commit_keeps_held
#print axioms RSure.commit_success
#print axioms RSure.commit_all_or_none
#print axioms RSure.commit_requires_single
#print axioms RSure.h1_pure
#print axioms RSure.h2a_caller_token
#print axioms RSure.h2b_delegated
#print axioms RSure.p2_await_then_commit
#print axioms RSure.commit_counts
