import RSure.Model.Types

namespace RSure.Model.Fund

open RSure.Model.Types

/-! The central fund cover, mirroring `16_fund.rho`: capped by balance and per-claim cap,
    one cover per claim, and a monotone governance nonce. -/

structure FundState where
  balance : Nat
  maxCover : Nat
  covers : List (Nat × Nat)
  govNonce : Nat
  deriving DecidableEq, Repr

def lookup (k : Nat) : List (Nat × Nat) → Option Nat
  | [] => none
  | (k', v) :: rest => if k = k' then some v else lookup k rest

def cover (s : FundState) (claimId amount nonce sigs : Nat) :
    Option (FundState × Nat) :=
  if nonce ≤ s.govNonce then none
  else if sigs < 2 then none
  else if lookup claimId s.covers ≠ none then none
  else if amount < 1 || amount > s.balance || amount > s.maxCover then none
  else
    some ({ s with
      balance := s.balance - amount
      covers := (claimId, amount) :: s.covers
      govNonce := nonce }, amount)

theorem fund_cover_bounds (s s' : FundState) (claimId amount nonce sigs paid : Nat)
    (h : cover s claimId amount nonce sigs = some (s', paid)) :
    1 ≤ amount ∧ amount ≤ s.balance ∧ amount ≤ s.maxCover := by
  by_cases hn : nonce ≤ s.govNonce
  · simp [cover, hn] at h
  · by_cases hs : sigs < 2
    · simp [cover, hn, hs] at h
    · by_cases hc : lookup claimId s.covers ≠ none
      · simp [cover, hn, hs, hc] at h
      · by_cases ha : amount < 1 || amount > s.balance || amount > s.maxCover
        · simp [cover, hn, hs, hc, ha] at h
        · have ha0 := ha
          simp only [Bool.or_eq_true, decide_eq_true_eq, not_or] at ha0
          omega

theorem fund_cover_records (s s' : FundState) (claimId amount nonce sigs paid : Nat)
    (h : cover s claimId amount nonce sigs = some (s', paid)) :
    paid = amount ∧ s'.balance = s.balance - amount ∧ s'.govNonce = nonce
      ∧ lookup claimId s'.covers = some amount := by
  by_cases hn : nonce ≤ s.govNonce
  · simp [cover, hn] at h
  · by_cases hs : sigs < 2
    · simp [cover, hn, hs] at h
    · by_cases hc : lookup claimId s.covers ≠ none
      · simp [cover, hn, hs, hc] at h
      · by_cases ha : amount < 1 || amount > s.balance || amount > s.maxCover
        · simp [cover, hn, hs, hc, ha] at h
        · simp [cover, hn, hs, hc, ha] at h
          rcases h with ⟨rfl, rfl⟩
          exact ⟨rfl, rfl, rfl, by simp [lookup]⟩

theorem fund_cover_le_balance (s s' : FundState) (claimId amount nonce sigs paid : Nat)
    (h : cover s claimId amount nonce sigs = some (s', paid)) :
    amount ≤ s.balance :=
  (fund_cover_bounds s s' claimId amount nonce sigs paid h).2.1

theorem fund_cover_le_cap (s s' : FundState) (claimId amount nonce sigs paid : Nat)
    (h : cover s claimId amount nonce sigs = some (s', paid)) :
    amount ≤ s.maxCover :=
  (fund_cover_bounds s s' claimId amount nonce sigs paid h).2.2

theorem fund_conserves (s s' : FundState) (claimId amount nonce sigs paid : Nat)
    (h : cover s claimId amount nonce sigs = some (s', paid)) :
    s'.balance + paid = s.balance := by
  have hb := fund_cover_bounds s s' claimId amount nonce sigs paid h
  have hr := fund_cover_records s s' claimId amount nonce sigs paid h
  rw [hr.2.1, hr.1]
  omega

theorem fund_cover_once (s s' : FundState) (claimId amount nonce sigs paid : Nat)
    (amount2 nonce2 sigs2 : Nat)
    (h : cover s claimId amount nonce sigs = some (s', paid)) :
    cover s' claimId amount2 nonce2 sigs2 = none := by
  have hr := fund_cover_records s s' claimId amount nonce sigs paid h
  unfold cover
  simp [hr.2.2.2]

end RSure.Model.Fund
