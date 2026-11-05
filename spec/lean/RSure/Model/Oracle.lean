import RSure.Model.Types
import RSure.Model.Claim

namespace RSure.Model.Oracle

open RSure.Model.Types

/-! The r-gen `OracleCase` boundary: a case is decided only for its named subject with a
    credential, executed once, and closed only after execution. -/

inductive OracleStatus where
  | open
  | decided
  | executed
  | closed
  deriving DecidableEq, Repr

structure OracleState where
  status : OracleStatus
  caseId : Nat
  subjectRef : Nat
  decision : Option Nat
  applied : Bool
  deriving DecidableEq, Repr

def decide (s : OracleState) (caseId subject outcome : Nat) (credentialOk : Bool) :
    Option OracleState :=
  if s.status = OracleStatus.open then
    if caseId = s.caseId then
      if subject = s.subjectRef then
        if credentialOk then
          some { s with status := OracleStatus.decided, decision := some outcome }
        else none
      else none
    else none
  else none

theorem oracle_decide_requires_credential (s s' : OracleState) (caseId subject outcome : Nat)
    (credentialOk : Bool) (h : decide s caseId subject outcome credentialOk = some s') :
    credentialOk = true ∧ caseId = s.caseId ∧ subject = s.subjectRef := by
  by_cases hs : s.status = OracleStatus.open
  · by_cases hc : caseId = s.caseId
    · by_cases hj : subject = s.subjectRef
      · by_cases hk : credentialOk
        · exact ⟨hk, hc, hj⟩
        · simp [decide, hs, hc, hj, hk] at h
      · simp [decide, hs, hc, hj] at h
    · simp [decide, hs, hc] at h
  · simp [decide, hs] at h

def execute (s : OracleState) (caseId : Nat) : Option OracleState :=
  if s.status = OracleStatus.decided then
    if caseId = s.caseId then
      some { s with status := OracleStatus.executed, applied := true }
    else none
  else none

theorem oracle_execute_once (s s' : OracleState) (caseId : Nat)
    (h : execute s caseId = some s') : execute s' caseId = none := by
  by_cases hs : s.status = OracleStatus.decided
  · by_cases hc : caseId = s.caseId
    · simp [execute, hs, hc] at h
      subst s'
      simp [execute]
    · simp [execute, hs, hc] at h
  · simp [execute, hs] at h

theorem oracle_execute_subject_bound (s s' : OracleState) (caseId : Nat)
    (h : execute s caseId = some s') :
    caseId = s.caseId ∧ s'.status = OracleStatus.executed ∧ s'.applied = true := by
  by_cases hs : s.status = OracleStatus.decided
  · by_cases hc : caseId = s.caseId
    · simp [execute, hs, hc] at h
      subst s'
      exact ⟨hc, rfl, rfl⟩
    · simp [execute, hs, hc] at h
  · simp [execute, hs] at h

theorem oracle_applied_matches (s s' : OracleState) (caseId : Nat)
    (h : execute s caseId = some s') : s'.applied = true :=
  (oracle_execute_subject_bound s s' caseId h).2.2

theorem oracle_apply_once (s s' : OracleState) (caseId : Nat)
    (h : execute s caseId = some s') : execute s' caseId = none :=
  oracle_execute_once s s' caseId h

def close (s : OracleState) : Option OracleState :=
  if s.status = OracleStatus.executed then
    some { s with status := OracleStatus.closed }
  else none

theorem oracle_close_requires_finished (s s' : OracleState)
    (h : close s = some s') : s.status = OracleStatus.executed := by
  by_cases he : s.status = OracleStatus.executed
  · exact he
  · simp [close, he] at h

/-! CP-14 OracleDecision. `RgenAdapter` verifies a credential or claim URI before the
    claim's `applyCap` can execute a decision. The adapter stores allow-listed URIs; the
    model proves the negative path (disabled or unregistered refuses) and the positive
    path (a verified decision is bound to the claim's oracle case). The r-gen truth of a
    credential is the `rgen.oracle_binding` boundary. -/

structure AdapterState where
  enabled : Bool
  strict : Bool
  credentials : List Nat
  claims : List Nat
  nonce : Nat
  deriving DecidableEq, Repr

def contains (k : Nat) : List Nat → Bool
  | [] => false
  | k' :: ks => if k = k' then true else contains k ks

def verifyCredential (s : AdapterState) (uri : Nat) : Option Nat :=
  if s.enabled = false then none
  else if s.strict then
    if contains uri s.credentials then some uri else none
  else some uri

def verifyClaim (s : AdapterState) (uri : Nat) : Option Nat :=
  if s.enabled = false then none
  else if s.strict then
    if contains uri s.claims then some uri else none
  else some uri

theorem adapter_verifyCredential_sound (s : AdapterState) (uri verified : Nat)
    (h : verifyCredential s uri = some verified) :
    s.enabled = true ∧ (s.strict = true → contains uri s.credentials = true) := by
  by_cases he : s.enabled = false
  · simp [verifyCredential, he] at h
  · have hen : s.enabled = true := by
      cases hb : s.enabled <;> simp_all
    refine ⟨hen, ?_⟩
    intro hstrict
    by_cases hc : contains uri s.credentials
    · exact hc
    · simp [verifyCredential, he, hstrict, hc] at h

theorem adapter_verifyClaim_sound (s : AdapterState) (uri verified : Nat)
    (h : verifyClaim s uri = some verified) :
    s.enabled = true ∧ (s.strict = true → contains uri s.claims = true) := by
  by_cases he : s.enabled = false
  · simp [verifyClaim, he] at h
  · have hen : s.enabled = true := by
      cases hb : s.enabled <;> simp_all
    refine ⟨hen, ?_⟩
    intro hstrict
    by_cases hc : contains uri s.claims
    · exact hc
    · simp [verifyClaim, he, hstrict, hc] at h

theorem adapter_refuses_disabled (s : AdapterState) (uri : Nat)
    (h : s.enabled = false) : verifyClaim s uri = none := by
  simp [verifyClaim, h]

theorem adapter_refuses_disabled_credential (s : AdapterState) (uri : Nat)
    (h : s.enabled = false) : verifyCredential s uri = none := by
  simp [verifyCredential, h]

theorem adapter_refuses_unregistered (s : AdapterState) (uri : Nat)
    (h : s.strict = true) (hc : contains uri s.claims = false) :
    verifyClaim s uri = none := by
  by_cases he : s.enabled = false
  · simp [verifyClaim, he]
  · simp [verifyClaim, he, h, hc]

theorem adapter_refuses_unregistered_credential (s : AdapterState) (uri : Nat)
    (h : s.strict = true) (hc : contains uri s.credentials = false) :
    verifyCredential s uri = none := by
  by_cases he : s.enabled = false
  · simp [verifyCredential, he]
  · simp [verifyCredential, he, h, hc]

/-- `applyCap@"applyDecision"` is exactly the claim adjudication step. -/
def applyCap (s : Claim.ClaimState) (caseId : Nat) (outcome : Claim.DecisionOutcome)
    (amount : Nat) : Option Claim.ClaimState :=
  Claim.applyDecision s caseId outcome amount

theorem oracle_applyCap_sound (s s' : Claim.ClaimState) (caseId : Nat)
    (outcome : Claim.DecisionOutcome) (amount : Nat)
    (hwf : Claim.ClaimWF s) (h : applyCap s caseId outcome amount = some s') :
    Claim.ClaimWF s' ∧ s.oracleCase = some caseId :=
  Claim.claim_applyDecision_sound s s' caseId outcome amount hwf h

theorem oracle_decision_sound (a : AdapterState) (uri verified : Nat)
    (s s' : Claim.ClaimState) (caseId : Nat) (outcome : Claim.DecisionOutcome)
    (amount : Nat) (hv : verifyClaim a uri = some verified)
    (hwf : Claim.ClaimWF s) (h : applyCap s caseId outcome amount = some s') :
    a.enabled = true ∧ s.oracleCase = some caseId := by
  have ha := adapter_verifyClaim_sound a uri verified hv
  have hc := oracle_applyCap_sound s s' caseId outcome amount hwf h
  exact ⟨ha.1, hc.2⟩

def rgenAdapter : AdapterState where
  enabled := true
  strict := true
  credentials := [11]
  claims := [22]
  nonce := 0

theorem adapter_reachable :
    ∃ verified, verifyClaim rgenAdapter 22 = some verified := by
  refine ⟨22, ?_⟩
  simp [verifyClaim, rgenAdapter, contains]

end RSure.Model.Oracle
