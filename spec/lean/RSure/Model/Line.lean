import RSure.Model.Types

namespace RSure.Model.Line

open RSure.Model.Types

/-! One policy-syndicate line, mirroring `14_line.rho`. A line pays at most once per claim
    and never pays more than its exposure. Release returns the unpaid exposure. -/

structure LineState where
  exposure : Nat
  paid : Nat
  credited : Nat
  paidFor : List (Nat × Nat)
  nonce : Nat
  status : LineStatus
  deriving DecidableEq, Repr

def lookup (k : Nat) : List (Nat × Nat) → Option Nat
  | [] => none
  | (k', v) :: rest => if k = k' then some v else lookup k rest

def LineWF (s : LineState) : Prop := s.paid ≤ s.exposure ∧ 0 < s.exposure

structure PayResult (s s' : LineState) (claimId amount : Nat) : Prop where
  paid_eq : s'.paid = s.paid + amount
  exposure_eq : s'.exposure = s.exposure
  paidFor_eq : s'.paidFor = (claimId, amount) :: s.paidFor
  status_eq : s'.status = LineStatus.bound
  amount_pos : 1 ≤ amount
  amount_le : amount ≤ s.exposure - s.paid

def pay (s : LineState) (claimId amount : Nat) (tokenOk : Bool) : Option LineState :=
  if tokenOk then
    if s.status = LineStatus.bound then
      if lookup claimId s.paidFor = none then
        if amount < 1 || amount > s.exposure - s.paid then none
        else
          some { s with
            paid := s.paid + amount
            paidFor := (claimId, amount) :: s.paidFor
            nonce := s.nonce + 1 }
      else none
    else none
  else none

theorem line_pay_fields (s s' : LineState) (claimId amount : Nat) (tokenOk : Bool)
    (h : pay s claimId amount tokenOk = some s') :
    PayResult s s' claimId amount := by
  by_cases ht : tokenOk
  · by_cases hs : s.status = LineStatus.bound
    · by_cases hl : lookup claimId s.paidFor = none
      · by_cases ha : amount < 1 || amount > s.exposure - s.paid
        · simp [pay, ht, hs, hl, ha] at h
        · simp [pay, ht, hs, hl, ha] at h
          subst s'
          have ha' : 1 ≤ amount ∧ amount ≤ s.exposure - s.paid := by
            have ha0 := ha
            simp only [Bool.or_eq_true, decide_eq_true_eq, not_or] at ha0
            omega
          exact { paid_eq := rfl, exposure_eq := rfl, paidFor_eq := rfl,
                  status_eq := rfl, amount_pos := ha'.1, amount_le := ha'.2 }
      · simp [pay, ht, hs, hl] at h
    · simp [pay, ht, hs] at h
  · simp [pay, ht] at h

theorem line_pay_bounded (s s' : LineState) (claimId amount : Nat) (tokenOk : Bool)
    (hwf : LineWF s) (h : pay s claimId amount tokenOk = some s') :
    LineWF s' := by
  have hp := line_pay_fields s s' claimId amount tokenOk h
  have hle := hp.amount_le
  unfold LineWF at hwf ⊢
  constructor
  · rw [hp.paid_eq, hp.exposure_eq]
    omega
  · rw [hp.exposure_eq]
    exact hwf.2

theorem line_pay_once (s s' : LineState) (claimId amount : Nat) (tokenOk : Bool)
    (h : pay s claimId amount tokenOk = some s') :
    pay s' claimId amount tokenOk = none := by
  have hp := line_pay_fields s s' claimId amount tokenOk h
  have hl : lookup claimId s'.paidFor = some amount := by
    rw [hp.paidFor_eq]
    simp [lookup]
  by_cases ht : tokenOk
  · simp [pay, ht, hp.status_eq, hl]
  · simp [pay, ht]

theorem line_pay_once_per_claim (s s' : LineState) (claimId amount amount2 : Nat)
    (tokenOk : Bool) (h : pay s claimId amount tokenOk = some s') :
    pay s' claimId amount2 tokenOk = none := by
  have hp := line_pay_fields s s' claimId amount tokenOk h
  have hl : lookup claimId s'.paidFor ≠ none := by
    rw [hp.paidFor_eq]
    simp [lookup]
  by_cases ht : tokenOk
  · simp [pay, ht, hp.status_eq, hl]
  · simp [pay, ht]

def release (s : LineState) (tokenOk : Bool) : Option (LineState × Nat) :=
  if tokenOk then
    if s.status = LineStatus.bound then
      some ({ s with status := LineStatus.released, nonce := s.nonce + 1 },
            s.exposure - s.paid)
    else none
  else none

theorem line_release_restores (s s' : LineState) (credit : Nat) (tokenOk : Bool)
    (_hwf : LineWF s) (h : release s tokenOk = some (s', credit)) :
    s'.status = LineStatus.released ∧ credit = s.exposure - s.paid
      ∧ s'.paid = s.paid ∧ s'.exposure = s.exposure := by
  by_cases ht : tokenOk
  · by_cases hs : s.status = LineStatus.bound
    · simp [release, ht, hs] at h
      rcases h with ⟨rfl, rfl⟩
      exact ⟨rfl, rfl, rfl, rfl⟩
    · simp [release, ht, hs] at h
  · simp [release, ht] at h

theorem line_invariant (s s' : LineState) (claimId amount : Nat) (tokenOk : Bool)
    (hwf : LineWF s) (h : pay s claimId amount tokenOk = some s') :
    s'.paid ≤ s'.exposure := (line_pay_bounded s s' claimId amount tokenOk hwf h).1

/-- `LineCredit@"credit"` deposits premium into the syndicate purse and records the local
    credit. The local counter is proved; the native move is `ertp.native_total`. -/
def credit (s : LineState) (tokenOk : Bool) (amount : Nat) :
    Option (LineState × Nat) :=
  if tokenOk then
    if s.status = LineStatus.bound then
      if amount < 1 then none
      else
        some ({ s with
                 credited := s.credited + amount
                 nonce := s.nonce + 1 }, amount)
    else none
  else none

theorem line_credit_sound (s s' : LineState) (tokenOk : Bool) (amount paid : Nat)
    (hwf : LineWF s) (h : credit s tokenOk amount = some (s', paid)) :
    LineWF s' ∧ paid = amount ∧ s'.credited = s.credited + amount
      ∧ s'.paid = s.paid ∧ s'.exposure = s.exposure := by
  by_cases ht : tokenOk
  · by_cases hs : s.status = LineStatus.bound
    · by_cases ha : amount < 1
      · simp [credit, ht, hs, ha] at h
      · simp [credit, ht, hs, ha] at h
        rcases h with ⟨rfl, rfl⟩
        refine ⟨hwf, rfl, rfl, rfl, rfl⟩
    · simp [credit, ht, hs] at h
  · simp [credit, ht] at h

/-- The credit conservation is conditional on the native total assumption. `nativeTotal`
    is the caller-supplied proposition that the ERTP move behind the credit conserved
    value; the local credited counter then moves by exactly the deposited amount. -/
theorem line_credit_conserves (nativeTotal : Prop) (hn : nativeTotal)
    (s s' : LineState) (tokenOk : Bool) (amount paid : Nat)
    (h : credit s tokenOk amount = some (s', paid)) :
    nativeTotal ∧ s'.credited = s.credited + amount ∧ paid = amount := by
  by_cases ht : tokenOk
  · by_cases hs : s.status = LineStatus.bound
    · by_cases ha : amount < 1
      · simp [credit, ht, hs, ha] at h
      · simp [credit, ht, hs, ha] at h
        rcases h with ⟨rfl, rfl⟩
        exact ⟨hn, rfl, rfl⟩
    · simp [credit, ht, hs] at h
  · simp [credit, ht] at h

theorem line_credit_refuses_token (s : LineState) (amount : Nat)
    (h : tokenOk = false) : credit s tokenOk amount = none := by
  simp [credit, h]

theorem line_credit_refuses_released (s : LineState) (tokenOk : Bool) (amount : Nat)
    (h : s.status = LineStatus.released) : credit s tokenOk amount = none := by
  by_cases ht : tokenOk
  · simp [credit, ht, h]
  · simp [credit, ht]

theorem line_credit_refuses_amount (s : LineState) (tokenOk : Bool) (amount : Nat)
    (h : amount < 1) : credit s tokenOk amount = none := by
  by_cases ht : tokenOk
  · by_cases hs : s.status = LineStatus.bound
    · simp [credit, ht, hs, h]
    · simp [credit, ht, hs]
  · simp [credit, ht]

theorem line_pay_sound (s s' : LineState) (claimId amount : Nat) (tokenOk : Bool)
    (hwf : LineWF s) (h : pay s claimId amount tokenOk = some s') :
    LineWF s' ∧ s'.paid = s.paid + amount ∧ amount ≤ s.exposure - s.paid := by
  have hp := line_pay_fields s s' claimId amount tokenOk h
  exact ⟨line_pay_bounded s s' claimId amount tokenOk hwf h, hp.paid_eq, hp.amount_le⟩

theorem line_pay_refuses_token (s : LineState) (claimId amount : Nat)
    (h : tokenOk = false) : pay s claimId amount tokenOk = none := by
  simp [pay, h]

theorem line_pay_refuses_claim (s : LineState) (claimId amount : Nat) (tokenOk : Bool)
    (h : lookup claimId s.paidFor ≠ none) :
    pay s claimId amount tokenOk = none := by
  by_cases ht : tokenOk
  · by_cases hs : s.status = LineStatus.bound
    · simp [pay, ht, hs, h]
    · simp [pay, ht, hs]
  · simp [pay, ht]

theorem line_release_refuses_token (s : LineState)
    (h : tokenOk = false) : release s tokenOk = none := by
  simp [release, h]

def payableLine : LineState where
  exposure := 500
  paid := 0
  credited := 0
  paidFor := []
  nonce := 0
  status := LineStatus.bound

theorem line_pay_reachable :
    ∃ s', pay payableLine 7 100 true = some s' ∧ s'.paid = 100 := by
  refine ⟨{ payableLine with paid := 100, paidFor := [(7, 100)], nonce := 1 }, ?_, rfl⟩
  simp [pay, payableLine, lookup]

theorem line_credit_reachable :
    ∃ s' paid, credit payableLine true 100 = some (s', paid) ∧ paid = 100 := by
  refine ⟨{ payableLine with credited := 100, nonce := 1 }, 100, ?_, rfl⟩
  simp [credit, payableLine]

end RSure.Model.Line
