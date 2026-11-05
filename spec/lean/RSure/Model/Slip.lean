import RSure.Basic
import RSure.Model.Types

namespace RSure.Model.Slip

open RSure
open RSure.Model.Types

/-! Placing-slip subscription and funding, mirroring `13_slip.rho`. A slip binds only when
    the insured has accepted, the premium is fully funded and subscriptions sum to 10000 bps.
    The model keeps share rates, not syndicate URIs. -/

structure SlipState where
  premiumTotal : Nat
  funded : Nat
  shares : List Nat
  insuredAccepted : Bool
  status : SlipStatus
  nonce : Nat
  deriving DecidableEq, Repr

def bind (s : SlipState) : Option SlipState :=
  if s.insuredAccepted then
    if s.funded = s.premiumTotal then
      if s.shares = [] then none
      else if sumNat s.shares = BPS then
        some { s with status := SlipStatus.bound, nonce := s.nonce + 1 }
      else none
    else none
  else none

theorem slip_bind_requires_subscription (s s' : SlipState) (h : bind s = some s') :
    s.insuredAccepted = true ∧ s.funded = s.premiumTotal
      ∧ s.shares ≠ [] ∧ sumNat s.shares = BPS := by
  by_cases ha : s.insuredAccepted
  · by_cases hf : s.funded = s.premiumTotal
    · by_cases he : s.shares = []
      · simp [bind, ha, hf, he] at h
      · by_cases hb : sumNat s.shares = BPS
        · exact ⟨ha, hf, he, hb⟩
        · simp [bind, ha, hf, he, hb] at h
    · simp [bind, ha, hf] at h
  · simp [bind, ha] at h

theorem slip_share_sum_bps (s s' : SlipState) (h : bind s = some s') :
    sumNat s.shares = BPS :=
  (slip_bind_requires_subscription s s' h).2.2.2

theorem slip_bind_moves (s s' : SlipState) (h : bind s = some s') :
    s'.status = SlipStatus.bound ∧ s'.funded = s.funded := by
  by_cases ha : s.insuredAccepted
  · by_cases hf : s.funded = s.premiumTotal
    · by_cases he : s.shares = []
      · simp [bind, ha, hf, he] at h
      · by_cases hb : sumNat s.shares = BPS
        · simp [bind, ha, hf, he, hb] at h
          subst s'
          exact ⟨rfl, hf.symm⟩
        · simp [bind, ha, hf, he, hb] at h
    · simp [bind, ha, hf] at h
  · simp [bind, ha] at h

def expire (s : SlipState) (nowPast : Bool) : Option (SlipState × Nat) :=
  if nowPast then
    if s.status = SlipStatus.bound then none
    else
      some ({ s with status := SlipStatus.expired, nonce := s.nonce + 1 }, s.funded)
  else none

theorem slip_expire_refund (s s' : SlipState) (credit : Nat) (nowPast : Bool)
    (h : expire s nowPast = some (s', credit)) :
    credit = s.funded := by
  by_cases hn : nowPast
  · by_cases hb : s.status = SlipStatus.bound
    · simp [expire, hn, hb] at h
    · simp [expire, hn, hb] at h
      rcases h with ⟨rfl, rfl⟩
      rfl
  · simp [expire, hn] at h

end RSure.Model.Slip
