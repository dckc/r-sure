namespace RSure.Model.Payments

/-! CP-03 PaymentsRail. The r-cash adapter surface `40_payments.rho`: an allow-listed
    asset resolves to an issuer, an owner account is created once, and a deposit facet is
    only exposed for a registered account on an allowed asset.

    Boundary: ERTP value conservation and purse custody are `ertp.native_total`. The
    `nativeOk` guard stands for "the native move conserves or fails"; every conservation
    result is conditional on it, while the local account bookkeeping is proved. -/

structure PaymentsState where
  assets : List Nat
  accounts : List (Nat × Nat)
  platformOwner : Nat
  nonce : Nat
  deriving DecidableEq, Repr

def assetAllowed (asset : Nat) : List Nat → Bool
  | [] => false
  | a :: rest => if asset = a then true else assetAllowed asset rest

def lookupBalance (owner : Nat) : List (Nat × Nat) → Option Nat
  | [] => none
  | (o, v) :: rest => if owner = o then some v else lookupBalance owner rest

def hasAccount (owner : Nat) (accounts : List (Nat × Nat)) : Bool :=
  match lookupBalance owner accounts with
  | some _ => true
  | none => false

def totalBalance : List (Nat × Nat) → Nat
  | [] => 0
  | (_, v) :: rest => v + totalBalance rest

/-- Replace the first entry for `owner`, or append one when absent. -/
def setBalance : List (Nat × Nat) → Nat → Nat → List (Nat × Nat)
  | [], owner, amount => [(owner, amount)]
  | (o, v) :: rest, owner, amount =>
      if owner = o then (owner, amount) :: rest
      else (o, v) :: setBalance rest owner amount

/-- The rail is well formed when at least one asset is allow-listed and a platform owner
    is configured. -/
def PaymentsWF (s : PaymentsState) : Prop :=
  s.assets ≠ [] ∧ s.platformOwner ≠ 0

def issuer (s : PaymentsState) (assetId : Nat) : Option Nat :=
  if assetAllowed assetId s.assets then some assetId else none

/-- `ensureAccount` is idempotent for a non-zero owner: the first call registers the
    owner, later calls return the same account id. -/
def ensureAccount (s : PaymentsState) (owner : Nat) : Option (PaymentsState × Nat) :=
  if owner = 0 then none
  else if hasAccount owner s.accounts then
    some (s, owner)
  else
    some ({ s with accounts := (owner, 0) :: s.accounts, nonce := s.nonce + 1 }, owner)

def depositFacet (s : PaymentsState) (owner assetId : Nat) : Option Nat :=
  if assetAllowed assetId s.assets then
    if hasAccount owner s.accounts then some owner else none
  else none

/-- A native deposit, guarded by the external `nativeOk` fact. The local balance moves by
    exactly `amount`; the boundary supplies the ERTP conservation premise. -/
def deposit (s : PaymentsState) (owner amount : Nat) (nativeOk : Bool) :
    Option (PaymentsState × Nat) :=
  if nativeOk = false then none
  else if amount < 1 then none
  else match lookupBalance owner s.accounts with
    | none => none
    | some old =>
        some ({ s with
                 accounts := setBalance s.accounts owner (old + amount)
                 nonce := s.nonce + 1 }, amount)

theorem payments_issuer_sound (s : PaymentsState) (assetId issuerId : Nat)
    (h : issuer s assetId = some issuerId) : assetAllowed assetId s.assets = true := by
  by_cases ha : assetAllowed assetId s.assets
  · exact ha
  · simp [issuer, ha] at h

theorem payments_issuer_refuses (s : PaymentsState) (assetId : Nat)
    (h : assetAllowed assetId s.assets = false) : issuer s assetId = none := by
  simp [issuer, h]

theorem payments_ensureAccount_sound (s s' : PaymentsState) (owner accountId : Nat)
    (h : ensureAccount s owner = some (s', accountId)) :
    accountId = owner ∧ hasAccount owner s'.accounts = true := by
  by_cases hz : owner = 0
  · simp [ensureAccount, hz] at h
  · by_cases hc : hasAccount owner s.accounts
    · simp [ensureAccount, hz, hc] at h
      rcases h with ⟨rfl, rfl⟩
      exact ⟨rfl, hc⟩
    · simp [ensureAccount, hz, hc] at h
      rcases h with ⟨rfl, rfl⟩
      simp [hasAccount, lookupBalance]

theorem payments_ensureAccount_refuses_zero (s : PaymentsState) (owner : Nat)
    (h : owner = 0) : ensureAccount s owner = none := by
  simp [ensureAccount, h]

theorem payments_ensureAccount_idempotent (s s' : PaymentsState) (owner accountId : Nat)
    (h : ensureAccount s owner = some (s', accountId))
    (hc : hasAccount owner s.accounts = true) :
    s' = s := by
  by_cases hz : owner = 0
  · simp [ensureAccount, hz] at h
  · simp [ensureAccount, hz, hc] at h
    exact h.1.symm

theorem payments_depositFacet_sound (s : PaymentsState) (owner assetId facet : Nat)
    (h : depositFacet s owner assetId = some facet) :
    assetAllowed assetId s.assets = true ∧ hasAccount owner s.accounts = true := by
  by_cases ha : assetAllowed assetId s.assets
  · by_cases hc : hasAccount owner s.accounts
    · exact ⟨ha, hc⟩
    · simp [depositFacet, ha, hc] at h
  · simp [depositFacet, ha] at h

theorem payments_depositFacet_refuses_asset (s : PaymentsState) (owner assetId : Nat)
    (h : assetAllowed assetId s.assets = false) :
    depositFacet s owner assetId = none := by
  simp [depositFacet, h]

theorem payments_depositFacet_refuses_account (s : PaymentsState) (owner assetId : Nat)
    (h : hasAccount owner s.accounts = false) :
    depositFacet s owner assetId = none := by
  by_cases ha : assetAllowed assetId s.assets
  · simp [depositFacet, ha, h]
  · simp [depositFacet, ha]

theorem payments_deposit_sound (s s' : PaymentsState) (owner amount paid : Nat)
    (nativeOk : Bool) (h : deposit s owner amount nativeOk = some (s', paid)) :
    paid = amount ∧ hasAccount owner s.accounts = true ∧ s'.nonce = s.nonce + 1 := by
  by_cases hn : nativeOk = false
  · simp [deposit, hn] at h
  · by_cases ha : amount < 1
    · simp [deposit, hn, ha] at h
    · cases hb : lookupBalance owner s.accounts with
      | none => simp [deposit, hn, ha, hb] at h
      | some old =>
          simp [deposit, hn, ha, hb] at h
          rcases h with ⟨rfl, rfl⟩
          exact ⟨rfl, by simp [hasAccount, hb], rfl⟩

theorem lookupBalance_le_total (accounts : List (Nat × Nat)) (owner old : Nat)
    (h : lookupBalance owner accounts = some old) :
    old ≤ totalBalance accounts := by
  induction accounts with
  | nil => simp [lookupBalance] at h
  | cons head rest ih =>
      rcases head with ⟨o, v⟩
      by_cases ho : owner = o
      · simp [lookupBalance, ho] at h
        have hv : v = old := by simpa using h
        subst old
        show v ≤ v + totalBalance rest
        omega
      · have hrest : lookupBalance owner rest = some old := by
          simpa [lookupBalance, ho] using h
        have hle := ih hrest
        show old ≤ v + totalBalance rest
        omega

theorem totalBalance_setBalance (accounts : List (Nat × Nat)) (owner old new : Nat)
    (h : lookupBalance owner accounts = some old) :
    totalBalance (setBalance accounts owner new) = totalBalance accounts - old + new := by
  induction accounts with
  | nil => simp [lookupBalance] at h
  | cons head rest ih =>
      rcases head with ⟨o, v⟩
      by_cases ho : owner = o
      · simp [lookupBalance, ho] at h
        have hv : v = old := by simpa using h
        subst old
        simp only [setBalance, ho, totalBalance]
        omega
      · have hrest : lookupBalance owner rest = some old := by
          simpa [lookupBalance, ho] using h
        have hih := ih hrest
        have hle := lookupBalance_le_total rest owner old hrest
        simp only [setBalance, ho, totalBalance, hih]
        omega

/-- Local account conservation for a native deposit. Conditional on `nativeOk`, which is
    the ERTP `ertp.native_total` boundary. -/
theorem payments_deposit_conserves (s s' : PaymentsState) (owner amount paid : Nat)
    (nativeOk : Bool) (h : deposit s owner amount nativeOk = some (s', paid)) :
    totalBalance s'.accounts = totalBalance s.accounts + amount := by
  by_cases hn : nativeOk = false
  · simp [deposit, hn] at h
  · by_cases ha : amount < 1
    · simp [deposit, hn, ha] at h
    · cases hb : lookupBalance owner s.accounts with
      | none => simp [deposit, hn, ha, hb] at h
      | some old =>
          simp [deposit, hn, ha, hb] at h
          rcases h with ⟨rfl, rfl⟩
          rw [totalBalance_setBalance s.accounts owner old (old + amount) hb]
          have hle := lookupBalance_le_total s.accounts owner old hb
          omega

theorem payments_refuses_native (s : PaymentsState) (owner amount : Nat) (nativeOk : Bool)
    (h : nativeOk = false) : deposit s owner amount nativeOk = none := by
  simp [deposit, h]

def initialPayments : PaymentsState where
  assets := [7]
  accounts := []
  platformOwner := 1
  nonce := 0

theorem payments_reachable :
    ∃ s', issuer initialPayments 7 = some s' := by
  refine ⟨7, ?_⟩
  simp [issuer, assetAllowed, initialPayments]

def accountPayments : PaymentsState :=
  { initialPayments with accounts := [(5, 0)], nonce := 1 }

theorem payments_ensureAccount_reachable :
    ∃ s' accountId, ensureAccount initialPayments 5 = some (s', accountId) :=
  ⟨accountPayments, 5,
   by simp [ensureAccount, hasAccount, lookupBalance, initialPayments, accountPayments]⟩

end RSure.Model.Payments
