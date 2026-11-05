import RSure.Basic

namespace RSure.Model.Terms

open RSure

/-! The ordered cover-terms validation surface from `03_terms.rho`, reduced to the
    economic fields. Strings, class names and evidence URIs are boundary values. -/

structure Terms where
  classOk : Bool
  assetLen : Nat
  aggregateLimit : Nat
  perClaimLimit : Nat
  deductible : Nat
  premiumTotal : Nat
  periodStartHeight : Nat
  periodEndHeight : Nat
  waitingBlocks : Nat
  noticeBlocks : Nat
  runOffBlocks : Nat
  standardClaimMax : Nat
  minSyndicates : Nat
  maxSyndicates : Nat
  brokerCommissionBps : Nat
  centralFundBps : Nat
  evidenceOk : Bool
  claimsLeadOk : Bool
  deriving DecidableEq, Repr

def between (x lo hi : Nat) : Bool := decide (lo ≤ x ∧ x ≤ hi)

def validate (t : Terms) : Bool :=
  t.classOk &&
  between t.assetLen 1 32 &&
  between t.aggregateLimit 1 1000000000000 &&
  between t.perClaimLimit 1 1000000000000 &&
  between t.deductible 0 1000000000000 &&
  between t.premiumTotal 1 1000000000000 &&
  between t.periodStartHeight 0 1000000000000 &&
  between t.periodEndHeight 1 1000000000000 &&
  between t.waitingBlocks 0 1000000 &&
  between t.noticeBlocks 0 1000000 &&
  between t.runOffBlocks 0 1000000 &&
  between t.standardClaimMax 0 1000000000000 &&
  between t.minSyndicates 1 8 &&
  between t.maxSyndicates 1 8 &&
  between t.brokerCommissionBps 0 10000 &&
  between t.centralFundBps 0 10000 &&
  decide (t.perClaimLimit ≤ t.aggregateLimit) &&
  decide (t.deductible < t.perClaimLimit) &&
  decide (t.standardClaimMax ≤ t.perClaimLimit) &&
  decide (t.minSyndicates ≤ t.maxSyndicates) &&
  decide (t.brokerCommissionBps + t.centralFundBps ≤ 3000) &&
  decide (t.periodStartHeight < t.periodEndHeight) &&
  t.evidenceOk &&
  t.claimsLeadOk

/-- The economic postcondition of validation. -/
structure TermsOk (t : Terms) : Prop where
  limits : t.perClaimLimit ≤ t.aggregateLimit
  deductible : t.deductible < t.perClaimLimit
  threshold : t.standardClaimMax ≤ t.perClaimLimit
  bps : t.brokerCommissionBps + t.centralFundBps ≤ 3000
  period : t.periodStartHeight < t.periodEndHeight

theorem terms_validate_sound (t : Terms) (h : validate t = true) : TermsOk t := by
  simp [validate, between] at h
  exact ⟨by omega, by omega, by omega, by omega, by omega⟩

theorem terms_validate_asset (t : Terms) (h : validate t = true) :
    1 ≤ t.assetLen ∧ t.assetLen ≤ 32 := by
  simp [validate, between] at h
  omega

end RSure.Model.Terms
