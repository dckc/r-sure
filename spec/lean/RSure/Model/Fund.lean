import RSure.Model.Types

namespace RSure.Model.Fund

open RSure.Model.Types

/-! The central fund cover, mirroring `16_fund.rho`: capped by balance and per-claim cap,
    one cover per claim, and a monotone governance nonce. -/

structure FundState where
  balance : Nat
  maxCover : Nat
  covers : List (Nat × Nat)
  contributions : List (Nat × Nat)
  admins : Nat
  threshold : Nat
  nonce : Nat
  govNonce : Nat
  deriving DecidableEq, Repr

/-- The fund's governance quorum is well formed. -/
def FundWF (s : FundState) : Prop := 2 ≤ s.threshold ∧ s.threshold ≤ s.admins

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

theorem fund_cover_admin_fields (s s' : FundState) (claimId amount nonce sigs paid : Nat)
    (h : cover s claimId amount nonce sigs = some (s', paid)) :
    s'.admins = s.admins ∧ s'.threshold = s.threshold ∧ s'.nonce = s.nonce := by
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
          exact ⟨rfl, rfl, rfl⟩

theorem fund_cover_sound (s s' : FundState) (claimId amount nonce sigs paid : Nat)
    (hwf : FundWF s) (h : cover s claimId amount nonce sigs = some (s', paid)) :
    FundWF s' ∧ s'.balance + paid = s.balance ∧ s'.admins = s.admins
      ∧ s'.threshold = s.threshold := by
  have hc := fund_conserves s s' claimId amount nonce sigs paid h
  have hf := fund_cover_admin_fields s s' claimId amount nonce sigs paid h
  refine ⟨?_, hc, hf.1, hf.2.1⟩
  refine ⟨?_, ?_⟩
  · rw [hf.2.1]
    exact hwf.1
  · rw [hf.2.1, hf.1]
    exact hwf.2

theorem fund_cover_refuses_signatures (s : FundState) (claimId amount nonce sigs : Nat)
    (h : sigs < 2) : cover s claimId amount nonce sigs = none := by
  by_cases hn : nonce ≤ s.govNonce
  · simp [cover, hn]
  · simp [cover, hn, h]

theorem fund_cover_refuses_amount (s : FundState) (claimId amount nonce sigs : Nat)
    (h : amount < 1 ∨ amount > s.balance ∨ amount > s.maxCover) :
    cover s claimId amount nonce sigs = none := by
  by_cases hn : nonce ≤ s.govNonce
  · simp [cover, hn]
  · by_cases hs : sigs < 2
    · simp [cover, hn, hs]
    · by_cases hc : lookup claimId s.covers ≠ none
      · simp [cover, hn, hs, hc]
      · have ha : (amount < 1 || amount > s.balance || amount > s.maxCover) = true := by
          rcases h with h | h | h
          · simp [h]
          · simp [h]
          · simp [h]
        simp [cover, hn, hs, hc, ha]

def lookupContribution (policyId : Nat) : List (Nat × Nat) → Option Nat
  | [] => none
  | (p, v) :: rest => if policyId = p then some v else lookupContribution policyId rest

def addContribution (policyId amount : Nat) : List (Nat × Nat) → List (Nat × Nat)
  | [] => [(policyId, amount)]
  | (p, v) :: rest =>
      if policyId = p then (p, v + amount) :: rest
      else (p, v) :: addContribution policyId amount rest

/-- `SureFund@"contribute"` deposits a premium levy. The native move is conditional on
    `ertp.native_total` (the `nativeOk` guard); the local balance and contribution ledger
    are proved. -/
def contribute (s : FundState) (policyId amount : Nat) (paused nativeOk : Bool) :
    Option (FundState × Nat) :=
  if paused then none
  else if nativeOk = false then none
  else if amount < 1 then none
  else
    some ({ s with
             balance := s.balance + amount
             contributions := addContribution policyId amount s.contributions
             nonce := s.nonce + 1 }, amount)

theorem fund_contribute_sound (s s' : FundState) (policyId amount paid : Nat)
    (paused nativeOk : Bool) (hwf : FundWF s)
    (h : contribute s policyId amount paused nativeOk = some (s', paid)) :
    FundWF s' ∧ paid = amount ∧ s'.balance = s.balance + amount
      ∧ s'.nonce = s.nonce + 1 := by
  by_cases hp : paused
  · simp [contribute, hp] at h
  · by_cases hn : nativeOk = false
    · simp [contribute, hp, hn] at h
    · by_cases ha : amount < 1
      · simp [contribute, hp, hn, ha] at h
      · simp [contribute, hp, hn, ha] at h
        rcases h with ⟨rfl, rfl⟩
        exact ⟨hwf, rfl, rfl, rfl⟩

theorem fund_contribute_refuses_paused (s : FundState) (policyId amount : Nat)
    (nativeOk : Bool) (h : paused = true) :
    contribute s policyId amount paused nativeOk = none := by
  simp [contribute, h]

theorem fund_contribute_refuses_native (s : FundState) (policyId amount : Nat)
    (paused : Bool) (h : nativeOk = false) :
    contribute s policyId amount paused nativeOk = none := by
  by_cases hp : paused
  · simp [contribute, hp]
  · simp [contribute, hp, h]

theorem fund_contribute_refuses_amount (s : FundState) (policyId amount : Nat)
    (paused nativeOk : Bool) (h : amount < 1) :
    contribute s policyId amount paused nativeOk = none := by
  by_cases hp : paused
  · simp [contribute, hp]
  · by_cases hn : nativeOk = false
    · simp [contribute, hp, hn]
    · simp [contribute, hp, hn, h]

inductive FundAction where
  | setParams
  | setAdmins
  deriving DecidableEq, Repr

/-- The `SureFund@"admin"` surface: parameter changes and quorum rotation, both behind a
    strictly increasing governance nonce and the fund threshold. -/
def admin (s : FundState) (nonce : Nat) (action : FundAction)
    (newAdmins newThreshold levy perClaim bps sigs : Nat) : Option FundState :=
  if nonce ≤ s.govNonce then none
  else if sigs < s.threshold then none
  else match action with
    | FundAction.setParams =>
        if levy ≤ 10000 ∧ bps ≤ 10000 then
          some { s with maxCover := perClaim, govNonce := nonce }
        else none
    | FundAction.setAdmins =>
        if 2 ≤ newThreshold ∧ newThreshold ≤ newAdmins then
          some { s with admins := newAdmins, threshold := newThreshold, govNonce := nonce }
        else none

theorem fund_admin_sound (s s' : FundState) (nonce : Nat) (action : FundAction)
    (newAdmins newThreshold levy perClaim bps sigs : Nat) (hwf : FundWF s)
    (h : admin s nonce action newAdmins newThreshold levy perClaim bps sigs = some s') :
    FundWF s' ∧ s'.govNonce = nonce := by
  by_cases hr : nonce ≤ s.govNonce
  · simp [admin, hr] at h
  · by_cases hq : sigs < s.threshold
    · simp [admin, hr, hq] at h
    · cases action with
      | setParams =>
          by_cases hv : levy ≤ 10000 ∧ bps ≤ 10000
          · simp [admin, hr, hq, hv] at h
            subst s'
            exact ⟨hwf, rfl⟩
          · simp [admin, hr, hq, hv] at h
      | setAdmins =>
          by_cases hv : 2 ≤ newThreshold ∧ newThreshold ≤ newAdmins
          · simp [admin, hr, hq, hv] at h
            subst s'
            exact ⟨hv, rfl⟩
          · simp [admin, hr, hq, hv] at h

theorem fund_admin_refuses_replay (s : FundState) (nonce : Nat) (action : FundAction)
    (newAdmins newThreshold levy perClaim bps sigs : Nat) (h : nonce ≤ s.govNonce) :
    admin s nonce action newAdmins newThreshold levy perClaim bps sigs = none := by
  simp [admin, h]

theorem fund_admin_refuses_threshold (s : FundState) (nonce : Nat) (action : FundAction)
    (newAdmins newThreshold levy perClaim bps sigs : Nat) (h : sigs < s.threshold) :
    admin s nonce action newAdmins newThreshold levy perClaim bps sigs = none := by
  by_cases hr : nonce ≤ s.govNonce
  · simp [admin, hr]
  · simp [admin, hr, h]

def healthyFund : FundState where
  balance := 1000
  maxCover := 500
  covers := []
  contributions := []
  admins := 3
  threshold := 2
  nonce := 0
  govNonce := 0

theorem fund_reachable :
    ∃ s' paid, cover healthyFund 7 100 1 2 = some (s', paid) ∧ paid = 100 := by
  refine ⟨{ healthyFund with balance := 900, covers := [(7, 100)], govNonce := 1 }, 100, ?_, rfl⟩
  simp [cover, healthyFund, lookup]

def contributedFund : FundState :=
  { healthyFund with
    balance := 1050
    contributions := [(3, 50)]
    nonce := 1 }

theorem fund_contribute_reachable :
    ∃ s' paid, contribute healthyFund 3 50 false true = some (s', paid)
      ∧ s'.balance = 1050 := by
  refine ⟨contributedFund, 50, ?_, rfl⟩
  simp [contribute, addContribution, healthyFund, contributedFund]

end RSure.Model.Fund
