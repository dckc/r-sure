namespace RSure.Model.Admin

/-! CP-02 AdminAuthority. `02_admin.rho` reduces to a threshold count over configured
    keys plus a strictly increasing governance nonce. `verify` is the AdminGuard result;
    `admin` is the SureAdmin mutation. The pause flag is the only authority effect that
    reaches the rest of the system.

    Boundary: secp256k1 verification, distinct-key validation and the deployer clock are
    assumed (`crypto.authority`, `deploy.atomicity`). `admins` counts distinct keys. -/

inductive AdminAction where
  | pauseAll
  | resumeAll
  | setAdmins
  | setThreshold
  deriving DecidableEq, Repr

structure AdminState where
  paused : Bool
  nonce : Nat
  admins : Nat
  threshold : Nat
  deriving DecidableEq, Repr

/-- Well-formed quorum: at least two signers are required, and the configured threshold
    does not exceed the number of configured keys. -/
def AdminWF (s : AdminState) : Prop := 2 ≤ s.threshold ∧ s.threshold ≤ s.admins

/-- AdminGuard.verify for one domain, nonce, action and signature set. The model keeps
    the signature count; the cryptographic check is the boundary. -/
def verify (s : AdminState) (_domain _nonce _action _args sigs : Nat) : Bool :=
  decide (s.threshold ≤ sigs)

def isPaused (s : AdminState) : Bool := s.paused

def admin (s : AdminState) (nonce : Nat) (action : AdminAction)
    (newAdmins newThreshold : Nat) (sigs : Nat) : Option AdminState :=
  if nonce ≤ s.nonce then none
  else if sigs < s.threshold then none
  else match action with
    | AdminAction.pauseAll =>
        some { s with paused := true, nonce := nonce }
    | AdminAction.resumeAll =>
        some { s with paused := false, nonce := nonce }
    | AdminAction.setAdmins =>
        if 2 ≤ newThreshold ∧ newThreshold ≤ newAdmins then
          some { s with admins := newAdmins, threshold := newThreshold, nonce := nonce }
        else none
    | AdminAction.setThreshold =>
        if 2 ≤ newThreshold ∧ newThreshold ≤ s.admins then
          some { s with threshold := newThreshold, nonce := nonce }
        else none

theorem admin_verify_sound (s : AdminState) (domain nonce action args sigs : Nat)
    (h : verify s domain nonce action args sigs = true) :
    s.threshold ≤ sigs := by
  unfold verify at h
  exact of_decide_eq_true h

theorem admin_sound (s s' : AdminState) (nonce : Nat) (action : AdminAction)
    (newAdmins newThreshold sigs : Nat) (hwf : AdminWF s)
    (h : admin s nonce action newAdmins newThreshold sigs = some s') :
    AdminWF s' ∧ s'.nonce = nonce ∧ s.nonce < nonce := by
  by_cases hr : nonce ≤ s.nonce
  · simp [admin, hr] at h
  · by_cases hq : sigs < s.threshold
    · simp [admin, hr, hq] at h
    · have hlt : s.nonce < nonce := by omega
      cases action with
      | pauseAll =>
          simp [admin, hr, hq] at h
          subst s'
          exact ⟨hwf, rfl, hlt⟩
      | resumeAll =>
          simp [admin, hr, hq] at h
          subst s'
          exact ⟨hwf, rfl, hlt⟩
      | setAdmins =>
          by_cases hv : 2 ≤ newThreshold ∧ newThreshold ≤ newAdmins
          · simp [admin, hr, hq, hv] at h
            subst s'
            exact ⟨hv, rfl, hlt⟩
          · simp [admin, hr, hq, hv] at h
      | setThreshold =>
          by_cases hv : 2 ≤ newThreshold ∧ newThreshold ≤ s.admins
          · simp [admin, hr, hq, hv] at h
            subst s'
            exact ⟨⟨hv.1, hv.2⟩, rfl, hlt⟩
          · simp [admin, hr, hq, hv] at h

theorem admin_pause_sound (s s' : AdminState) (nonce : Nat) (newAdmins newThreshold sigs : Nat)
    (hwf : AdminWF s)
    (h : admin s nonce AdminAction.pauseAll newAdmins newThreshold sigs = some s') :
    s'.paused = true ∧ s'.nonce = nonce := by
  by_cases hr : nonce ≤ s.nonce
  · simp [admin, hr] at h
  · by_cases hq : sigs < s.threshold
    · simp [admin, hr, hq] at h
    · simp [admin, hr, hq] at h
      subst s'
      exact ⟨rfl, rfl⟩

theorem admin_refuses_replay (s : AdminState) (nonce : Nat) (action : AdminAction)
    (newAdmins newThreshold sigs : Nat) (h : nonce ≤ s.nonce) :
    admin s nonce action newAdmins newThreshold sigs = none := by
  simp [admin, h]

theorem admin_refuses_threshold (s : AdminState) (nonce : Nat) (action : AdminAction)
    (newAdmins newThreshold sigs : Nat) (h : sigs < s.threshold) :
    admin s nonce action newAdmins newThreshold sigs = none := by
  by_cases hr : nonce ≤ s.nonce
  · simp [admin, hr]
  · simp [admin, hr, h]

theorem admin_refuses_quorum (s : AdminState) (nonce : Nat)
    (newAdmins newThreshold sigs : Nat) (h : newThreshold < 2) :
    admin s nonce AdminAction.setAdmins newAdmins newThreshold sigs = none := by
  by_cases hr : nonce ≤ s.nonce
  · simp [admin, hr]
  · by_cases hq : sigs < s.threshold
    · simp [admin, hr, hq]
    · have hv : ¬ (2 ≤ newThreshold ∧ newThreshold ≤ newAdmins) := by omega
      simp [admin, hr, hq, hv]

theorem admin_isPaused_truthful (s : AdminState) :
    isPaused s = true ↔ s.paused = true := by
  simp [isPaused]

/-- The pause flag is a source-visible projection of admin state. It is not a proof that
    the Rholang wiring consults it; that is the `pause.contract` boundary and the
    `unit_pause_scope` suite. -/
theorem admin_pause_blocks_new_risk (s : AdminState) (h : isPaused s = true) :
    s.paused = true := by
  unfold isPaused at h
  exact h

def initialAdmin : AdminState where
  paused := false
  nonce := 0
  admins := 3
  threshold := 2

def pausedAdmin : AdminState :=
  { initialAdmin with paused := true, nonce := 1 }

theorem admin_reachable :
    ∃ s', admin initialAdmin 1 AdminAction.pauseAll 0 0 2 = some s' ∧ s'.paused = true :=
  ⟨pausedAdmin, by simp [admin, initialAdmin, pausedAdmin],
   by simp [pausedAdmin]⟩

end RSure.Model.Admin
