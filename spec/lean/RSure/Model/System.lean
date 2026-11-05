import RSure.Basic
import RSure.Model.Math
import RSure.Model.Types
import RSure.Model.Line
import RSure.Model.Claim
import RSure.Model.Policy
import RSure.Model.Fund

namespace RSure.Model.System

open RSure
open RSure.Model.Math
open RSure.Model.Types
open RSure.Model.Claim
open RSure.Model.Policy
open RSure.Model.Fund

/-! Composed settlement and the atomicity boundary. A settlement pays the payable from the
    central-fund cover plus the line plan; the two-cell transfer models a value move that
    either commits wholly or is refused before any effect. -/

structure TwoCell where
  left : Nat
  right : Nat
  deriving DecidableEq, Repr

def transfer (s : TwoCell) (amount : Nat) : Option TwoCell :=
  if amount > s.left then none
  else some { left := s.left - amount, right := s.right + amount }

theorem system_step_atomic (s s' : TwoCell) (amount : Nat)
    (h : transfer s amount = some s') :
    s'.left + s'.right = s.left + s.right := by
  by_cases ha : amount > s.left
  · simp [transfer, ha] at h
  · simp [transfer, ha] at h
    subst s'
    change (s.left - amount) + (s.right + amount) = s.left + s.right
    omega

theorem system_step_refuses (s : TwoCell) (amount : Nat) (h : amount > s.left) :
    transfer s amount = none := by
  simp [transfer, h]

theorem system_settlement_conserves (payable cover : Nat) (bpses : List Nat)
    (hcov : cover ≤ payable)
    (hfit : allocFits (payable - cover) bpses 0) :
    cover + sumNat (alloc (payable - cover) bpses) = payable := by
  rw [math_alloc_sums (payable - cover) bpses hfit]
  omega

theorem system_settlement_plan (payable cover : Nat) (bpses : List Nat)
    (_hcov : cover ≤ payable)
    (hfit : allocFits (payable - cover) bpses 0) :
    sumNat (alloc (payable - cover) bpses) = payable - cover :=
  math_alloc_sums (payable - cover) bpses hfit

/-! Composed settlement: `Claim -> Policy -> lines -> Fund`. The line plan is represented
    by one aggregate line book (the per-line model is `Model.Line`). The composed step calls
    the actual `Policy.settleClaim`, `Claim.settleExact` and `Fund.cover` functions, so the
    conservation and exactly-once theorems are about the composition, not fresh arithmetic. -/

structure LineBook where
  exposure : Nat
  paid : Nat
  paidFor : List (Nat × Nat)
  deriving DecidableEq, Repr

def bookLookup (k : Nat) : List (Nat × Nat) → Option Nat
  | [] => none
  | (k', v) :: rest => if k = k' then some v else bookLookup k rest

def LineBookWF (b : LineBook) : Prop := b.paid ≤ b.exposure

def payBook (b : LineBook) (claimId amount : Nat) : Option LineBook :=
  if amount < 1 || b.paid + amount > b.exposure then none
  else if bookLookup claimId b.paidFor ≠ none then none
  else
    some { b with
      paid := b.paid + amount
      paidFor := (claimId, amount) :: b.paidFor }

theorem book_pay_fields (b b' : LineBook) (claimId amount : Nat)
    (h : payBook b claimId amount = some b') :
    b'.paid = b.paid + amount
      ∧ bookLookup claimId b.paidFor = none
      ∧ bookLookup claimId b'.paidFor = some amount := by
  by_cases ha : amount < 1 || b.paid + amount > b.exposure
  · simp [payBook, ha] at h
  · by_cases hc : bookLookup claimId b.paidFor ≠ none
    · simp [payBook, ha, hc] at h
    · simp [payBook, ha, hc] at h
      subst b'
      exact ⟨rfl, by simpa using hc, by simp [bookLookup]⟩

theorem book_pay_exposure (b b' : LineBook) (claimId amount : Nat)
    (h : payBook b claimId amount = some b') : b'.exposure = b.exposure := by
  by_cases ha : amount < 1 || b.paid + amount > b.exposure
  · simp [payBook, ha] at h
  · by_cases hc : bookLookup claimId b.paidFor ≠ none
    · simp [payBook, ha, hc] at h
    · simp [payBook, ha, hc] at h
      subst b'
      rfl

theorem book_pay_sound (b b' : LineBook) (claimId amount : Nat)
    (hwf : LineBookWF b) (h : payBook b claimId amount = some b') :
    LineBookWF b' ∧ b'.paid = b.paid + amount := by
  have hf := book_pay_fields b b' claimId amount h
  have hex := book_pay_exposure b b' claimId amount h
  refine ⟨?_, hf.1⟩
  unfold LineBookWF at hwf ⊢
  rw [hf.1, hex]
  by_cases ha : amount < 1 || b.paid + amount > b.exposure
  · simp [payBook, ha] at h
  · have ha' : ¬ (amount < 1 ∨ b.paid + amount > b.exposure) := by
      intro hbad
      apply ha
      rcases hbad with hbad | hbad
      · simp [hbad]
      · simp [hbad]
    omega

theorem book_pay_once (b b' : LineBook) (claimId amount : Nat)
    (h : payBook b claimId amount = some b') :
    payBook b' claimId amount = none := by
  have hf := book_pay_fields b b' claimId amount h
  have hl : bookLookup claimId b'.paidFor ≠ none := by
    rw [hf.2.2]
    simp [bookLookup]
  simp [payBook, hl]

structure EngineState where
  claim : ClaimState
  policy : PolicyState
  book : LineBook
  fund : FundState
  deriving DecidableEq, Repr

def EngineWF (e : EngineState) : Prop :=
  ClaimWF e.claim ∧ PolicyWF e.policy ∧ LineBookWF e.book ∧ FundWF e.fund

def fundStep (f : FundState) (covered : Bool) (claimId coverAmount nonce sigs : Nat) :
    Option (FundState × Nat) :=
  if covered then Fund.cover f claimId coverAmount nonce sigs
  else some (f, 0)

theorem fundStep_conserves (f f' : FundState) (covered : Bool) (claimId coverAmount
    nonce sigs cover : Nat)
    (h : fundStep f covered claimId coverAmount nonce sigs = some (f', cover)) :
    f'.balance + cover = f.balance := by
  by_cases hc : covered
  · simp [fundStep, hc] at h
    exact fund_conserves f f' claimId coverAmount nonce sigs cover h
  · simp [fundStep, hc] at h
    rcases h with ⟨rfl, rfl⟩
    omega

def settlementPayable (e : EngineState) (agreed : Nat) : Nat :=
  payable agreed e.policy.perClaimLimit e.policy.aggregateRemaining e.policy.deductible

theorem fundStep_sound (f f' : FundState) (covered : Bool) (claimId coverAmount
    nonce sigs cover : Nat) (hwf : FundWF f)
    (h : fundStep f covered claimId coverAmount nonce sigs = some (f', cover)) :
    FundWF f' := by
  by_cases hc : covered
  · simp [fundStep, hc] at h
    exact (fund_cover_sound f f' claimId coverAmount nonce sigs cover hwf h).1
  · simp [fundStep, hc] at h
    rcases h with ⟨rfl, _⟩
    exact hwf

def settleEngine (e : EngineState) (claimId agreed coverAmount nonce sigs : Nat)
    (covered : Bool) : Option (EngineState × Nat × Nat) :=
  if ClaimStatus.terminal e.claim.status then none
  else if agreed ≠ e.claim.agreedAmount then none
  else if e.claim.status = ClaimStatus.agreed || e.claim.status = ClaimStatus.upheld
      || e.claim.status = ClaimStatus.partiallyUpheld then
    let pay := settlementPayable e agreed
    if pay > e.policy.aggregateRemaining then none
    else match Policy.settleClaim e.policy claimId agreed with
      | none => none
      | some policy' =>
          match fundStep e.fund covered claimId coverAmount nonce sigs with
          | none => none
          | some (fund', cover) =>
              if cover > pay then none
              else if pay - cover > e.book.exposure - e.book.paid then none
              else match Claim.settleExact e.claim pay with
                | none => none
                | some claim' =>
                    match payBook e.book claimId (pay - cover) with
                    | none => none
                    | some book' =>
                        some ({ claim := claim', policy := policy',
                                book := book', fund := fund' }, pay, cover)
  else none

theorem system_composition_sound (e e' : EngineState) (claimId agreed coverAmount
    nonce sigs pay cover : Nat) (covered : Bool) (hwf : EngineWF e)
    (h : settleEngine e claimId agreed coverAmount nonce sigs covered = some (e', pay, cover)) :
    EngineWF e'
      ∧ e'.claim.status = ClaimStatus.settled
      ∧ e'.claim.paid = pay
      ∧ e'.book.paid = e.book.paid + (pay - cover)
      ∧ e'.fund.balance + cover = e.fund.balance
      ∧ e'.policy.aggregateRemaining + pay = e.policy.aggregateRemaining
      ∧ pay ≤ agreed ∧ pay ≤ e.policy.perClaimLimit
      ∧ pay ≤ e.policy.aggregateRemaining := by
  by_cases ht : ClaimStatus.terminal e.claim.status
  · simp [settleEngine, ht] at h
  · by_cases hga : agreed ≠ e.claim.agreedAmount
    · simp [settleEngine, ht, hga] at h
    · by_cases hs : e.claim.status = ClaimStatus.agreed
          || e.claim.status = ClaimStatus.upheld
          || e.claim.status = ClaimStatus.partiallyUpheld
      · by_cases hgt : settlementPayable e agreed > e.policy.aggregateRemaining
        · simp [settleEngine, ht, hga, hs, hgt] at h
        · cases hp : Policy.settleClaim e.policy claimId agreed with
          | none => simp [settleEngine, ht, hga, hs, hgt, hp] at h
          | some policy' =>
              cases hf : fundStep e.fund covered claimId coverAmount nonce sigs with
              | none => simp [settleEngine, ht, hga, hs, hgt, hp, hf] at h
              | some fc =>
                  rcases fc with ⟨fund', cover'⟩
                  by_cases hcov : cover' > settlementPayable e agreed
                  · simp [settleEngine, ht, hga, hs, hgt, hp, hf, hcov] at h
                  · by_cases hline : settlementPayable e agreed - cover'
                        > e.book.exposure - e.book.paid
                    · simp [settleEngine, ht, hga, hs, hgt, hp, hf, hcov, hline] at h
                    · cases hc : Claim.settleExact e.claim (settlementPayable e agreed) with
                      | none =>
                          simp [settleEngine, ht, hga, hs, hgt, hp, hf, hcov, hline, hc] at h
                      | some claim' =>
                          cases hb : payBook e.book claimId
                              (settlementPayable e agreed - cover') with
                          | none =>
                              simp [settleEngine, ht, hga, hs, hgt, hp, hf, hcov, hline,
                                hc, hb] at h
                          | some book' =>
                              simp [settleEngine, ht, hga, hs, hgt, hp, hf, hcov, hline,
                                hc, hb] at h
                              rcases h with ⟨rfl, rfl, rfl⟩
                              have hclaim := Claim.claim_settleExact_sound e.claim claim'
                                (settlementPayable e agreed) hwf.1 hc
                              have hpolicy := Policy.policy_settle_remaining e.policy policy'
                                claimId agreed hp
                              have hpolicy_wf := (Policy.policy_settle_sound e.policy policy'
                                claimId agreed hwf.2.1 hp).1
                              have hbook := book_pay_fields e.book book' claimId
                                (settlementPayable e agreed - cover') hb
                              have hbook_wf := (book_pay_sound e.book book' claimId
                                (settlementPayable e agreed - cover') hwf.2.2.1 hb).1
                              have hfund_wf := fundStep_sound e.fund fund' covered claimId
                                coverAmount nonce sigs cover' hwf.2.2.2 hf
                              have hfund := fundStep_conserves e.fund fund' covered claimId
                                coverAmount nonce sigs cover' hf
                              have hpay_bound := math_payable_le_aggregate agreed
                                e.policy.perClaimLimit e.policy.aggregateRemaining
                                e.policy.deductible
                              refine ⟨⟨hclaim.1, hpolicy_wf, hbook_wf, hfund_wf⟩,
                                hclaim.2.1, hclaim.2.2.1, ?_, ?_, ?_, ?_, ?_, ?_⟩
                              · rw [hbook.1]
                              · exact hfund
                              · rw [hpolicy]
                                change e.policy.aggregateRemaining
                                  - payable agreed e.policy.perClaimLimit
                                      e.policy.aggregateRemaining e.policy.deductible
                                  + payable agreed e.policy.perClaimLimit
                                      e.policy.aggregateRemaining e.policy.deductible
                                  = e.policy.aggregateRemaining
                                omega
                              · exact math_payable_le_agreed agreed
                                  e.policy.perClaimLimit e.policy.aggregateRemaining
                                  e.policy.deductible
                              · exact math_payable_le_perClaim agreed e.policy.perClaimLimit
                                  e.policy.aggregateRemaining e.policy.deductible
                              · exact hpay_bound
      · simp [settleEngine, ht, hga, hs] at h

theorem system_composition_once (e e' : EngineState) (claimId agreed coverAmount
    nonce sigs pay cover : Nat) (covered : Bool) (hwf : EngineWF e)
    (h : settleEngine e claimId agreed coverAmount nonce sigs covered = some (e', pay, cover)) :
    settleEngine e' claimId agreed coverAmount nonce sigs covered = none := by
  have hs := (system_composition_sound e e' claimId agreed coverAmount nonce sigs pay cover
    covered hwf h).2.1
  simp [settleEngine, hs, ClaimStatus.terminal]

theorem system_composition_refuses_terminal (e : EngineState) (claimId agreed coverAmount
    nonce sigs : Nat) (covered : Bool) (h : ClaimStatus.terminal e.claim.status = true) :
    settleEngine e claimId agreed coverAmount nonce sigs covered = none := by
  simp [settleEngine, h]

def engineClaim : ClaimState :=
  { kind := some ClaimKind.standard
    status := ClaimStatus.agreed
    leadManager := 1
    secondManager := 2
    agreedAmount := 700
    claimedAmount := 1000
    assessmentAmount := 700
    assessmentPresent := true
    leadAgreed := true
    secondAgreed := true
    oracleCase := none
    appliedCase := none
    paid := 0 }

def engine : EngineState where
  claim := engineClaim
  policy := Policy.activePolicy
  book := { exposure := 1000, paid := 0, paidFor := [] }
  fund := Fund.healthyFund

def settledEngine : EngineState where
  claim := { engineClaim with status := ClaimStatus.settled, paid := 600 }
  policy := { Policy.activePolicy with
              aggregatePaid := 600
              aggregateRemaining := 400
              settledClaims := [7]
              nonce := 1 }
  book := { exposure := 1000, paid := 600, paidFor := [(7, 600)] }
  fund := Fund.healthyFund

theorem system_composition_reachable :
    ∃ e' pay cover, settleEngine engine 7 700 100 1 2 false = some (e', pay, cover)
      ∧ pay = 600 ∧ cover = 0 := by
  refine ⟨settledEngine, 600, 0, ?_, rfl, rfl⟩
  simp [settleEngine, settlementPayable, engine, engineClaim, settledEngine,
    fundStep, Policy.activePolicy, Policy.settleClaim, Policy.contains, payable,
    payableBase, Claim.settleExact, ClaimStatus.terminal, payBook, bookLookup]

end RSure.Model.System
