import RSure.Model.Types

namespace RSure.Model.Claim

open RSure.Model.Types

/-! Claim classification, lead/follow agreement, adjudication and settlement, mirroring
    `18_claim.rho`. The model follows the deployed guards; the missing terminal guard on
    `agree` is recorded as a counterexample rather than silently repaired. -/

inductive ClaimKind where
  | standard
  | complex
  deriving DecidableEq, Repr

inductive DecisionOutcome where
  | uphold
  | partiallyUpheld
  | revoke
  deriving DecidableEq, Repr

structure ClaimState where
  kind : Option ClaimKind
  status : ClaimStatus
  leadManager : Nat
  secondManager : Nat
  agreedAmount : Nat
  claimedAmount : Nat
  assessmentAmount : Nat
  assessmentPresent : Bool
  leadAgreed : Bool
  secondAgreed : Bool
  oracleCase : Option Nat
  appliedCase : Option Nat
  paid : Nat
  deriving DecidableEq, Repr

structure AgreeArgs where
  caller : Nat
  amount : Nat
  basisHash : Nat
  deriving DecidableEq, Repr

def agree (s : ClaimState) (a : AgreeArgs) : Option ClaimState :=
  if ClaimStatus.terminal s.status then none
  else match s.kind with
  | none => none
  | some ClaimKind.standard =>
      if a.caller = s.leadManager then
        some { s with
          status := ClaimStatus.agreed
          agreedAmount := a.amount
          leadAgreed := true }
      else none
  | some ClaimKind.complex =>
      if a.caller = s.leadManager then
        some { s with status := ClaimStatus.assessing, leadAgreed := true }
      else if a.caller = s.secondManager then
        if s.leadAgreed then
          some { s with
            status := ClaimStatus.agreed
            agreedAmount := a.amount
            secondAgreed := true }
        else none
      else none

theorem claim_agree_standard_lead (s s' : ClaimState) (a : AgreeArgs)
    (h : agree s a = some s') (hk : s.kind = some ClaimKind.standard) :
    a.caller = s.leadManager ∧ s'.status = ClaimStatus.agreed
      ∧ s'.agreedAmount = a.amount := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [agree, ht] at h
  · by_cases hc : a.caller = s.leadManager
    · simp [agree, ht, hk, hc] at h
      subst s'
      exact ⟨hc, rfl, rfl⟩
    · simp [agree, ht, hk, hc] at h

theorem claim_agree_complex_quorum (s s' : ClaimState) (a : AgreeArgs)
    (h : agree s a = some s') (hk : s.kind = some ClaimKind.complex)
    (hs : s'.status = ClaimStatus.agreed) :
    a.caller = s.secondManager ∧ s.leadAgreed = true
      ∧ s'.agreedAmount = a.amount := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [agree, ht] at h
  · by_cases hl : a.caller = s.leadManager
    · simp [agree, ht, hk, hl] at h
      subst s'
      simp at hs
    · by_cases hs2 : a.caller = s.secondManager
      · by_cases hlead : s.leadAgreed
        · simp [agree, ht, hk, hl] at h
          simp [hs2] at h
          simp [hlead] at h
          subst s'
          exact ⟨hs2, hlead, rfl⟩
        · simp [agree, ht, hk, hl] at h
          simp [hs2] at h
          simp [hlead] at h
      · simp [agree, ht, hk, hl] at h
        simp [hs2] at h

theorem claim_agree_complex_requires_lead (s s' : ClaimState) (a : AgreeArgs)
    (h : agree s a = some s') (hk : s.kind = some ClaimKind.complex)
    (hs : s'.status = ClaimStatus.agreed) :
    s.leadAgreed = true :=
  (claim_agree_complex_quorum s s' a h hk hs).2.1

def settle (s : ClaimState) : Option ClaimState :=
  if s.status = ClaimStatus.agreed || s.status = ClaimStatus.upheld
      || s.status = ClaimStatus.partiallyUpheld then
    some { s with status := ClaimStatus.settled, paid := s.agreedAmount }
  else none

theorem claim_settle_once (s s' : ClaimState) (h : settle s = some s') :
    settle s' = none := by
  by_cases hs : s.status = ClaimStatus.agreed || s.status = ClaimStatus.upheld
      || s.status = ClaimStatus.partiallyUpheld
  · simp [settle, hs] at h
    subst s'
    simp [settle]
  · simp [settle, hs] at h

theorem claim_paid_le_agreed (s s' : ClaimState) (h : settle s = some s') :
    s'.paid ≤ s'.agreedAmount := by
  by_cases hs : s.status = ClaimStatus.agreed || s.status = ClaimStatus.upheld
      || s.status = ClaimStatus.partiallyUpheld
  · simp [settle, hs] at h
    subst s'
    simp
  · simp [settle, hs] at h

theorem claim_terminal_sticky (s : ClaimState) (h : s.status = ClaimStatus.settled) :
    settle s = none := by
  simp [settle, h]

def applyDecision (s : ClaimState) (caseId : Nat) (outcome : DecisionOutcome)
    (amount : Nat) : Option ClaimState :=
  if ClaimStatus.terminal s.status then none
  else if s.oracleCase ≠ some caseId then none
  else if outcome = DecisionOutcome.uphold then
    if s.assessmentPresent then
      some { s with
        status := ClaimStatus.upheld
        agreedAmount := s.assessmentAmount
        appliedCase := some caseId }
    else none
  else if outcome = DecisionOutcome.partiallyUpheld then
    if amount ≤ s.claimedAmount then
      some { s with
        status := ClaimStatus.partiallyUpheld
        agreedAmount := amount
        appliedCase := some caseId }
    else none
  else if outcome = DecisionOutcome.revoke then
    some { s with
      status := ClaimStatus.denied
      agreedAmount := 0
      appliedCase := some caseId }
  else none

theorem claim_apply_case_bound (s s' : ClaimState) (caseId : Nat)
    (outcome : DecisionOutcome) (amount : Nat)
    (h : applyDecision s caseId outcome amount = some s') :
    s.oracleCase = some caseId := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [applyDecision, ht] at h
  · cases hcase : s.oracleCase with
    | none => simp [applyDecision, ht, hcase] at h
    | some cid =>
        by_cases hcid : cid = caseId
        · simp [hcid]
        · simp [applyDecision, ht, hcase, hcid] at h

theorem claim_apply_uphold (s s' : ClaimState) (caseId amount : Nat)
    (h : applyDecision s caseId DecisionOutcome.uphold amount = some s') :
    s'.status = ClaimStatus.upheld ∧ s'.agreedAmount = s.assessmentAmount := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [applyDecision, ht] at h
  · cases hcase : s.oracleCase with
    | none => simp [applyDecision, ht, hcase] at h
    | some cid =>
        by_cases hcid : cid = caseId
        · by_cases ha : s.assessmentPresent
          · simp [applyDecision, ht, hcase, hcid, ha] at h
            subst s'
            exact ⟨rfl, rfl⟩
          · simp [applyDecision, ht, hcase, hcid, ha] at h
        · simp [applyDecision, ht, hcase, hcid] at h

theorem claim_apply_partial (s s' : ClaimState) (caseId amount : Nat)
    (h : applyDecision s caseId DecisionOutcome.partiallyUpheld amount = some s') :
    amount ≤ s.claimedAmount ∧ s'.status = ClaimStatus.partiallyUpheld
      ∧ s'.agreedAmount = amount := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [applyDecision, ht] at h
  · cases hcase : s.oracleCase with
    | none => simp [applyDecision, ht, hcase] at h
    | some cid =>
        by_cases hcid : cid = caseId
        · by_cases ha : amount ≤ s.claimedAmount
          · simp [applyDecision, ht, hcase, hcid, ha] at h
            subst s'
            exact ⟨ha, rfl, rfl⟩
          · simp [applyDecision, ht, hcase, hcid, ha] at h
        · simp [applyDecision, ht, hcase, hcid] at h

theorem claim_apply_revoke (s s' : ClaimState) (caseId amount : Nat)
    (h : applyDecision s caseId DecisionOutcome.revoke amount = some s') :
    s'.status = ClaimStatus.denied ∧ s'.agreedAmount = 0 := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [applyDecision, ht] at h
  · cases hcase : s.oracleCase with
    | none => simp [applyDecision, ht, hcase] at h
    | some cid =>
        by_cases hcid : cid = caseId
        · simp [applyDecision, ht, hcase, hcid] at h
          subst s'
          exact ⟨rfl, rfl⟩
        · simp [applyDecision, ht, hcase, hcid] at h

def settledStandardClaim : ClaimState where
  kind := some ClaimKind.standard
  status := ClaimStatus.settled
  leadManager := 1
  secondManager := 2
  agreedAmount := 10
  claimedAmount := 10
  assessmentAmount := 10
  assessmentPresent := true
  leadAgreed := true
  secondAgreed := true
  oracleCase := none
  appliedCase := none
  paid := 10

/-- A terminal claim cannot be re-agreed. -/
theorem claim_agree_terminal (s : ClaimState) (a : AgreeArgs)
    (h : ClaimStatus.terminal s.status = true) : agree s a = none := by
  simp [agree, h]

/-- A terminal claim cannot be re-adjudicated. -/
theorem claim_applyDecision_terminal (s : ClaimState) (caseId : Nat)
    (outcome : DecisionOutcome) (amount : Nat)
    (h : ClaimStatus.terminal s.status = true) :
    applyDecision s caseId outcome amount = none := by
  simp [applyDecision, h]

end RSure.Model.Claim
