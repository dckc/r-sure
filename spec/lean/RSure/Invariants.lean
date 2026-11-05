import RSure.Model.Syndicate
import RSure.Model.Slip
import RSure.Model.Math
import RSure.Model.Policy
import RSure.Model.Line
import RSure.Model.Claim
import RSure.Model.System
import RSure.Model.Boundary

namespace RSure
namespace Invariants

/-! Documentation aliases. Flow rules and `claims.yaml` cite the underlying theorems, not
    these definitions, because `check_flows.py --strict` requires a theorem target. -/

def INV1_capacity := @Model.Syndicate.synd_quote_WF
def INV2_subscription := @Model.Slip.slip_bind_requires_subscription
def INV3_exposure := @Model.Math.math_alloc_sums
def INV4_premium := @Model.Policy.policy_distribute_conserves
def INV5_payable := @Model.Math.math_payable_le_aggregate
def INV6_settlement := @Model.System.system_settlement_conserves
def INV7_line := @Model.Line.line_pay_bounded
def INV8_once := @Model.Line.line_pay_once
def INV9_aggregate := @Model.Policy.policy_settle_aggregate
def INV10_terminal := @Model.Claim.claim_agree_terminal
def INV11_atomicity := @Model.System.system_step_atomic
def INV12_pause := Model.Boundary.assumed.pauseGate

end Invariants
end RSure
