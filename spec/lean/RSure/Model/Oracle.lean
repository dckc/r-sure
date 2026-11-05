import RSure.Model.Types

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

end RSure.Model.Oracle
