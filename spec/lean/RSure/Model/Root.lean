namespace RSure.Model.Root

/-! CP-01 RootAuthority. A shallow state machine for the installer-gated component
    directory `00_root.rho`. Entries are a function from component keys to records, so the
    model has no separate uniqueness proof burden. The authority invariant is that every
    registered version is positive and that the admin quorum is well formed (2-of-N with
    N at least the threshold).

    Boundary: installer identity, deployer pubkeys, 2-of-3 signatures and deploy rollback
    are assumed (`crypto.authority`, `deploy.atomicity`). The deployed `rotate` arm does
    not sanity-check `newVersion`; the model adds `1 ≤ newVersion` so the positive-version
    invariant is meaningful. That stronger model guard is recorded as a refinement gap. -/

inductive EntryStatus where
  | active
  | retired
  deriving DecidableEq, Repr

structure Entry where
  uri : Nat
  version : Nat
  status : EntryStatus
  deriving DecidableEq, Repr

structure RootState where
  entries : Nat → Option Entry
  frozen : Bool
  govNonce : Nat
  admins : Nat
  threshold : Nat

def put (entries : Nat → Option Entry) (key : Nat) (entry : Entry) :
    Nat → Option Entry :=
  fun k => if k = key then some entry else entries k

theorem root_put_same (entries : Nat → Option Entry) (key : Nat) (entry : Entry) :
    put entries key entry key = some entry := by
  simp [put]

theorem root_put_other (entries : Nat → Option Entry) (key j : Nat) (entry : Entry)
    (h : j ≠ key) : put entries key entry j = entries j := by
  simp [put, h]

/-- Authority safety: every stored version is positive, and the signer quorum is well
    formed. `admins` is the number of distinct configured keys. -/
def RootWF (s : RootState) : Prop :=
  (∀ k e, s.entries k = some e → 1 ≤ e.version)
    ∧ 2 ≤ s.threshold
    ∧ s.threshold ≤ s.admins

inductive RootAction where
  | setAdmins
  | setThreshold
  deriving DecidableEq, Repr

def register (s : RootState) (key uri version : Nat) (installerOk : Bool) :
    Option RootState :=
  if s.frozen then none
  else if installerOk = false then none
  else if version < 1 then none
  else if s.entries key ≠ none then none
  else
    some { s with
      entries := put s.entries key
        { uri := uri, version := version, status := EntryStatus.active } }

def rotate (s : RootState) (key expected newUri newVersion nonce : Nat)
    (adminOk : Bool) : Option RootState :=
  if nonce ≤ s.govNonce then none
  else if adminOk = false then none
  else if newVersion < 1 then none
  else match s.entries key with
    | none => none
    | some entry =>
        if entry.version ≠ expected then none
        else
          some { s with
            entries := put s.entries key
              { entry with uri := newUri, version := newVersion }
            govNonce := nonce }

def freeze (s : RootState) (nonce : Nat) (adminOk : Bool) : Option RootState :=
  if nonce ≤ s.govNonce then none
  else if adminOk = false then none
  else some { s with frozen := true, govNonce := nonce }

def admin (s : RootState) (nonce : Nat) (action : RootAction)
    (newAdmins newThreshold : Nat) (adminOk : Bool) : Option RootState :=
  if nonce ≤ s.govNonce then none
  else if adminOk = false then none
  else match action with
    | RootAction.setAdmins =>
        if 2 ≤ newThreshold ∧ newThreshold ≤ newAdmins then
          some { s with admins := newAdmins, threshold := newThreshold, govNonce := nonce }
        else none
    | RootAction.setThreshold =>
        if 2 ≤ newThreshold ∧ newThreshold ≤ s.admins then
          some { s with threshold := newThreshold, govNonce := nonce }
        else none

theorem root_register_sound (s s' : RootState) (key uri version : Nat)
    (installerOk : Bool) (hwf : RootWF s) (h : register s key uri version installerOk = some s') :
    RootWF s'
      ∧ s'.entries key = some { uri := uri, version := version, status := EntryStatus.active }
      ∧ s'.frozen = s.frozen
      ∧ s'.govNonce = s.govNonce
      ∧ s'.admins = s.admins
      ∧ s'.threshold = s.threshold := by
  by_cases hf : s.frozen
  · simp [register, hf] at h
  · by_cases hi : installerOk = false
    · simp [register, hf, hi] at h
    · by_cases hv : version < 1
      · simp [register, hf, hi, hv] at h
      · by_cases hd : s.entries key ≠ none
        · simp [register, hf, hi, hv, hd] at h
        · simp [register, hf, hi, hv, hd] at h
          have hfr : s.frozen = false := by simpa using hf
          subst s'
          have hv' : 1 ≤ version := by omega
          refine ⟨?_, ?_, ?_, rfl, rfl, rfl⟩
          · refine ⟨?_, hwf.2.1, hwf.2.2⟩
            intro k e he
            by_cases hk : k = key
            · subst hk
              simp [put] at he
              subst e
              exact hv'
            · have he' : s.entries k = some e := by
                simpa [put, hk] using he
              exact hwf.1 k e he'
          · simp [put]
          · simp [hfr]

theorem root_rotate_sound (s s' : RootState) (key expected newUri newVersion nonce : Nat)
    (adminOk : Bool) (hwf : RootWF s)
    (h : rotate s key expected newUri newVersion nonce adminOk = some s') :
    RootWF s' ∧ s'.govNonce = nonce ∧ s'.admins = s.admins
      ∧ s'.threshold = s.threshold ∧ s'.frozen = s.frozen := by
  by_cases hr : nonce ≤ s.govNonce
  · simp [rotate, hr] at h
  · by_cases ha : adminOk = false
    · simp [rotate, hr, ha] at h
    · by_cases hv : newVersion < 1
      · simp [rotate, hr, ha, hv] at h
      · cases he : s.entries key with
        | none => simp [rotate, hr, ha, hv, he] at h
        | some entry =>
            by_cases hstale : entry.version ≠ expected
            · simp [rotate, hr, ha, hv, he, hstale] at h
            · simp [rotate, hr, ha, hv, he, hstale] at h
              subst s'
              have hv' : 1 ≤ newVersion := by omega
              refine ⟨?_, rfl, rfl, rfl, rfl⟩
              · refine ⟨?_, hwf.2.1, hwf.2.2⟩
                intro k e hk
                by_cases hke : k = key
                · subst hke
                  simp [put] at hk
                  subst e
                  exact hv'
                · have hk' : s.entries k = some e := by
                    simpa [put, hke] using hk
                  exact hwf.1 k e hk'

theorem root_freeze_sound (s s' : RootState) (nonce : Nat) (adminOk : Bool)
    (hwf : RootWF s) (h : freeze s nonce adminOk = some s') :
    RootWF s' ∧ s'.frozen = true ∧ s'.govNonce = nonce
      ∧ s'.entries = s.entries ∧ s'.admins = s.admins
      ∧ s'.threshold = s.threshold := by
  by_cases hr : nonce ≤ s.govNonce
  · simp [freeze, hr] at h
  · by_cases ha : adminOk = false
    · simp [freeze, hr, ha] at h
    · simp [freeze, hr, ha] at h
      subst s'
      exact ⟨hwf, rfl, rfl, rfl, rfl, rfl⟩

theorem root_admin_sound (s s' : RootState) (nonce : Nat) (action : RootAction)
    (newAdmins newThreshold : Nat) (adminOk : Bool) (hwf : RootWF s)
    (h : admin s nonce action newAdmins newThreshold adminOk = some s') :
    RootWF s' ∧ s'.govNonce = nonce ∧ s'.entries = s.entries
      ∧ s'.frozen = s.frozen := by
  by_cases hr : nonce ≤ s.govNonce
  · simp [admin, hr] at h
  · by_cases ha : adminOk = false
    · simp [admin, hr, ha] at h
    · cases action with
      | setAdmins =>
          by_cases hq : 2 ≤ newThreshold ∧ newThreshold ≤ newAdmins
          · simp [admin, hr, ha, hq] at h
            subst s'
            exact ⟨⟨hwf.1, hq.1, hq.2⟩, rfl, rfl, rfl⟩
          · simp [admin, hr, ha, hq] at h
      | setThreshold =>
          by_cases hq : 2 ≤ newThreshold ∧ newThreshold ≤ s.admins
          · simp [admin, hr, ha, hq] at h
            subst s'
            exact ⟨⟨hwf.1, hq.1, hq.2⟩, rfl, rfl, rfl⟩
          · simp [admin, hr, ha, hq] at h

theorem root_register_refuses_frozen (s : RootState) (key uri version : Nat)
    (installerOk : Bool) (h : s.frozen = true) :
    register s key uri version installerOk = none := by
  simp [register, h]

theorem root_register_refuses_installer (s : RootState) (key uri version : Nat)
    (installerOk : Bool) (h : installerOk = false) :
    register s key uri version installerOk = none := by
  simp [register, h]

theorem root_register_refuses_duplicate (s : RootState) (key uri version : Nat)
    (installerOk : Bool) (h : s.entries key ≠ none) :
    register s key uri version installerOk = none := by
  by_cases hf : s.frozen
  · simp [register, hf]
  · by_cases hi : installerOk = false
    · simp [register, hf, hi]
    · by_cases hv : version < 1
      · simp [register, hf, hi, hv]
      · simp [register, hf, hi, hv, h]

theorem root_rotate_refuses_replay (s : RootState) (key expected newUri newVersion nonce : Nat)
    (adminOk : Bool) (h : nonce ≤ s.govNonce) :
    rotate s key expected newUri newVersion nonce adminOk = none := by
  simp [rotate, h]

theorem root_rotate_refuses_admin (s : RootState) (key expected newUri newVersion nonce : Nat)
    (adminOk : Bool) (h : adminOk = false) :
    rotate s key expected newUri newVersion nonce adminOk = none := by
  by_cases hr : nonce ≤ s.govNonce
  · simp [rotate, hr]
  · simp [rotate, hr, h]

theorem root_freeze_refuses_admin (s : RootState) (nonce : Nat) (adminOk : Bool)
    (h : adminOk = false) : freeze s nonce adminOk = none := by
  by_cases hr : nonce ≤ s.govNonce
  · simp [freeze, hr]
  · simp [freeze, hr, h]

theorem root_admin_refuses_replay (s : RootState) (nonce : Nat) (action : RootAction)
    (newAdmins newThreshold : Nat) (adminOk : Bool) (h : nonce ≤ s.govNonce) :
    admin s nonce action newAdmins newThreshold adminOk = none := by
  simp [admin, h]

theorem root_admin_refuses_threshold (s : RootState) (nonce : Nat) (action : RootAction)
    (newAdmins newThreshold : Nat) (adminOk : Bool)
    (h : adminOk = false) :
    admin s nonce action newAdmins newThreshold adminOk = none := by
  by_cases hr : nonce ≤ s.govNonce
  · simp [admin, hr]
  · simp [admin, hr, h]

def initialRoot : RootState where
  entries := fun _ => none
  frozen := false
  govNonce := 0
  admins := 3
  threshold := 2

def registeredRoot : RootState where
  entries := put initialRoot.entries 1
    { uri := 10, version := 1, status := EntryStatus.active }
  frozen := false
  govNonce := 0
  admins := 3
  threshold := 2

theorem root_register_reachable :
    ∃ s', register initialRoot 1 10 1 true = some s' :=
  ⟨registeredRoot, by simp [register, initialRoot, registeredRoot, put]⟩

theorem root_freeze_reachable :
    ∃ s', freeze initialRoot 1 true = some s' :=
  ⟨{ initialRoot with frozen := true, govNonce := 1 },
   by simp [freeze, initialRoot]⟩

theorem root_authority_reachable :
    ∃ s', register initialRoot 1 10 1 true = some s' ∧ s'.entries 1 ≠ none :=
  ⟨registeredRoot,
   by simp [register, initialRoot, registeredRoot, put],
   by simp [registeredRoot, put]⟩

end RSure.Model.Root
