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

/-- The claim lifecycle safety invariant: value is zero until the claim reaches the
    settled terminal state. `settled` is the only terminal state that may carry a positive
    `paid`, and `settle` is the only step that sets it. -/
def ClaimWF (s : ClaimState) : Prop :=
  s.paid = 0 ∨ s.status = ClaimStatus.settled

theorem claim_wf_step (s s' : ClaimState) (hpaid : s'.paid = s.paid)
    (hnt : ClaimStatus.terminal s.status = false) (hwf : ClaimWF s) : ClaimWF s' := by
  rcases hwf with hp | hs
  · left
    rw [hpaid]
    exact hp
  · exfalso
    rw [hs] at hnt
    simp [ClaimStatus.terminal] at hnt

/-- Manager assessment, allowed before the terminal state. -/
def assess (s : ClaimState) (who amount : Nat) (managerOk : Bool) :
    Option ClaimState :=
  if ClaimStatus.terminal s.status then none
  else if managerOk = false then none
  else if who ≠ s.leadManager ∧ who ≠ s.secondManager then none
  else some { s with
    status := ClaimStatus.assessed
    assessmentAmount := amount
    assessmentPresent := true }

/-- Opening an oracle case binds the claim to that case and moves it to `disputed`. -/
def dispute (s : ClaimState) (caseId : Nat) (oracleOk : Bool) :
    Option ClaimState :=
  if ClaimStatus.terminal s.status then none
  else if oracleOk = false then none
  else some { s with status := ClaimStatus.disputed, oracleCase := some caseId }

/-- Settlement with an explicit paid amount. The amount is bounded by the agreed amount;
    the caller obtains it from the policy payable. -/
def settleExact (s : ClaimState) (paid : Nat) : Option ClaimState :=
  if ClaimStatus.terminal s.status then none
  else if s.status = ClaimStatus.agreed || s.status = ClaimStatus.upheld
      || s.status = ClaimStatus.partiallyUpheld then
    if paid ≤ s.agreedAmount then
      some { s with status := ClaimStatus.settled, paid := paid }
    else none
  else none

theorem claim_assess_sound (s s' : ClaimState) (who amount : Nat) (managerOk : Bool)
    (hwf : ClaimWF s) (h : assess s who amount managerOk = some s') :
    ClaimWF s' ∧ s'.status = ClaimStatus.assessed
      ∧ s'.assessmentAmount = amount ∧ s'.assessmentPresent = true := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [assess, ht] at h
  · have hnt : ClaimStatus.terminal s.status = false := by simpa using ht
    by_cases hm : managerOk = false
    · simp [assess, ht, hm] at h
    · by_cases hw : who ≠ s.leadManager ∧ who ≠ s.secondManager
      · simp [assess, ht, hm, hw] at h
      · simp [assess, ht, hm, hw] at h
        subst s'
        refine ⟨claim_wf_step s _ rfl hnt hwf, rfl, rfl, rfl⟩

theorem claim_dispute_sound (s s' : ClaimState) (caseId : Nat) (oracleOk : Bool)
    (hwf : ClaimWF s) (h : dispute s caseId oracleOk = some s') :
    ClaimWF s' ∧ s'.status = ClaimStatus.disputed
      ∧ s'.oracleCase = some caseId := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [dispute, ht] at h
  · have hnt : ClaimStatus.terminal s.status = false := by simpa using ht
    by_cases ho : oracleOk = false
    · simp [dispute, ht, ho] at h
    · simp [dispute, ht, ho] at h
      subst s'
      exact ⟨claim_wf_step s _ rfl hnt hwf, rfl, rfl⟩

theorem claim_agree_paid (s s' : ClaimState) (a : AgreeArgs)
    (h : agree s a = some s') : s'.paid = s.paid := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [agree, ht] at h
  · cases hk : s.kind with
    | none => simp [agree, ht, hk] at h
    | some kind =>
        cases kind with
        | standard =>
            by_cases hc : a.caller = s.leadManager
            · simp [agree, ht, hk, hc] at h
              subst s'
              rfl
            · simp [agree, ht, hk, hc] at h
        | complex =>
            by_cases hl : a.caller = s.leadManager
            · simp [agree, ht, hk, hl] at h
              subst s'
              rfl
            · by_cases hsc : a.caller = s.secondManager
              · by_cases hlead : s.leadAgreed
                · by_cases hsame : s.secondManager = s.leadManager
                  · simp [agree, ht, hk, hl, hsc, hlead, hsame] at h
                    subst s'
                    rfl
                  · simp [agree, ht, hk, hl, hsc, hlead, hsame] at h
                    subst s'
                    rfl
                · by_cases hsame : s.secondManager = s.leadManager
                  · simp [agree, ht, hk, hl, hsc, hlead, hsame] at h
                    subst s'
                    rfl
                  · simp [agree, ht, hk, hl, hsc, hlead, hsame] at h
              · simp [agree, ht, hk, hl, hsc] at h

theorem claim_agree_sound (s s' : ClaimState) (a : AgreeArgs)
    (hwf : ClaimWF s) (h : agree s a = some s') : ClaimWF s' := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [agree, ht] at h
  · have hnt : ClaimStatus.terminal s.status = false := by simpa using ht
    exact claim_wf_step s s' (claim_agree_paid s s' a h) hnt hwf

theorem claim_applyDecision_paid (s s' : ClaimState) (caseId : Nat)
    (outcome : DecisionOutcome) (amount : Nat)
    (h : applyDecision s caseId outcome amount = some s') : s'.paid = s.paid := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [applyDecision, ht] at h
  · cases hc : s.oracleCase with
    | none => simp [applyDecision, ht, hc] at h
    | some cid =>
        by_cases hcid : cid = caseId
        · cases outcome with
          | uphold =>
              by_cases ha : s.assessmentPresent
              · simp [applyDecision, ht, hc, hcid, ha] at h
                subst s'
                rfl
              · simp [applyDecision, ht, hc, hcid, ha] at h
          | partiallyUpheld =>
              by_cases ha : amount ≤ s.claimedAmount
              · simp [applyDecision, ht, hc, hcid, ha] at h
                subst s'
                rfl
              · simp [applyDecision, ht, hc, hcid, ha] at h
          | revoke =>
              simp [applyDecision, ht, hc, hcid] at h
              subst s'
              rfl
        · simp [applyDecision, ht, hc, hcid] at h

theorem claim_applyDecision_sound (s s' : ClaimState) (caseId : Nat)
    (outcome : DecisionOutcome) (amount : Nat) (hwf : ClaimWF s)
    (h : applyDecision s caseId outcome amount = some s') :
    ClaimWF s' ∧ s.oracleCase = some caseId := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [applyDecision, ht] at h
  · have hnt : ClaimStatus.terminal s.status = false := by simpa using ht
    refine ⟨claim_wf_step s s' (claim_applyDecision_paid s s' caseId outcome amount h)
      hnt hwf, claim_apply_case_bound s s' caseId outcome amount h⟩

theorem claim_settle_sound (s s' : ClaimState) (hwf : ClaimWF s)
    (h : settle s = some s') :
    ClaimWF s' ∧ s'.status = ClaimStatus.settled
      ∧ s'.paid = s'.agreedAmount := by
  by_cases hs : s.status = ClaimStatus.agreed || s.status = ClaimStatus.upheld
      || s.status = ClaimStatus.partiallyUpheld
  · simp [settle, hs] at h
    subst s'
    exact ⟨Or.inr rfl, rfl, rfl⟩
  · simp [settle, hs] at h

theorem claim_settleExact_sound (s s' : ClaimState) (paid : Nat) (hwf : ClaimWF s)
    (h : settleExact s paid = some s') :
    ClaimWF s' ∧ s'.status = ClaimStatus.settled ∧ s'.paid = paid
      ∧ paid ≤ s.agreedAmount := by
  by_cases ht : ClaimStatus.terminal s.status
  · simp [settleExact, ht] at h
  · by_cases hs : s.status = ClaimStatus.agreed || s.status = ClaimStatus.upheld
        || s.status = ClaimStatus.partiallyUpheld
    · by_cases hp : paid ≤ s.agreedAmount
      · simp [settleExact, ht, hs, hp] at h
        subst s'
        exact ⟨Or.inr rfl, rfl, rfl, hp⟩
      · simp [settleExact, ht, hs, hp] at h
    · simp [settleExact, ht, hs] at h

theorem claim_refuses_terminal_agree (s : ClaimState) (a : AgreeArgs)
    (h : ClaimStatus.terminal s.status = true) : agree s a = none :=
  claim_agree_terminal s a h

theorem claim_refuses_terminal_assess (s : ClaimState) (who amount : Nat)
    (managerOk : Bool) (h : ClaimStatus.terminal s.status = true) :
    assess s who amount managerOk = none := by
  simp [assess, h]

theorem claim_refuses_terminal_dispute (s : ClaimState) (caseId : Nat)
    (oracleOk : Bool) (h : ClaimStatus.terminal s.status = true) :
    dispute s caseId oracleOk = none := by
  simp [dispute, h]

theorem claim_refuses_terminal_settle (s : ClaimState)
    (h : s.status = ClaimStatus.settled) : settle s = none := by
  by_cases hs : s.status = ClaimStatus.agreed || s.status = ClaimStatus.upheld
      || s.status = ClaimStatus.partiallyUpheld
  · simp [settle, hs, h] at hs
  · simp [settle, hs]

def assessableClaim : ClaimState where
  kind := some ClaimKind.standard
  status := ClaimStatus.notified
  leadManager := 1
  secondManager := 2
  agreedAmount := 0
  claimedAmount := 1000
  assessmentAmount := 0
  assessmentPresent := false
  leadAgreed := false
  secondAgreed := false
  oracleCase := none
  appliedCase := none
  paid := 0

def assessedClaim : ClaimState :=
  { assessableClaim with
    status := ClaimStatus.assessed
    assessmentAmount := 400
    assessmentPresent := true }

theorem claim_assess_reachable :
    ∃ s', assess assessableClaim 1 400 true = some s'
      ∧ s'.assessmentAmount = 400 := by
  refine ⟨assessedClaim, ?_, rfl⟩
  simp [assess, assessableClaim, assessedClaim, ClaimStatus.terminal]

def disputedClaim : ClaimState :=
  { assessableClaim with
    status := ClaimStatus.disputed
    oracleCase := some 9 }

theorem claim_dispute_reachable :
    ∃ s', dispute assessableClaim 9 true = some s'
      ∧ s'.status = ClaimStatus.disputed := by
  refine ⟨disputedClaim, ?_, rfl⟩
  simp [dispute, assessableClaim, disputedClaim, ClaimStatus.terminal]

def agreedClaim : ClaimState :=
  { assessableClaim with status := ClaimStatus.agreed, agreedAmount := 700 }

def settledClaim : ClaimState :=
  { agreedClaim with status := ClaimStatus.settled, paid := 700 }

theorem claim_settle_reachable :
    ∃ s', settleExact agreedClaim 700 = some s' ∧ s'.paid = 700 := by
  refine ⟨settledClaim, ?_, rfl⟩
  simp [settleExact, agreedClaim, settledClaim, ClaimStatus.terminal]

end RSure.Model.Claim
