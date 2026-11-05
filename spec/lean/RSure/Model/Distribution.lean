import RSure.Basic
import RSure.Model.Math
import RSure.Model.Types

namespace RSure.Model.Distribution

open RSure
open RSure.Model.Math
open RSure.Model.Types

/-! Premium distribution, mirroring `15_distribution.rho`. The plan allocates the base and
    the last bucket absorbs the remainder; `run` pays the plan exactly once. -/

structure DistributionState where
  base : Nat
  plan : List (Nat × Nat)
  status : DistributionStatus
  nonce : Nat
  deriving DecidableEq, Repr

def sumPlan : List (Nat × Nat) → Nat
  | [] => 0
  | (_, v) :: rest => v + sumPlan rest

def buildPlanAux (base : Nat) : List Nat → Nat → Nat → List (Nat × Nat)
  | [], _, _ => []
  | [_b], i, paid => [(i, base - paid)]
  | b :: bs, i, paid =>
      (i, share base b) :: buildPlanAux base bs (i + 1) (paid + share base b)

def buildPlan (base : Nat) (bpses : List Nat) : List (Nat × Nat) :=
  buildPlanAux base bpses 0 0

theorem distribution_planAux_sums (base : Nat) :
    ∀ (bpses : List Nat) (i paid : Nat), allocFits base bpses paid →
      sumPlan (buildPlanAux base bpses i paid) = base - paid := by
  intro bpses
  induction bpses with
  | nil =>
      intro i paid h
      simp [buildPlanAux, sumPlan, allocFits] at h ⊢
      omega
  | cons b bs ih =>
      intro i paid h
      cases bs with
      | nil => simp [buildPlanAux, sumPlan]
      | cons c cs =>
          simp only [buildPlanAux, allocFits, sumPlan] at h ⊢
          rw [ih (i + 1) (paid + share base b) h.2]
          omega

theorem distribution_plan_sums (base : Nat) (bpses : List Nat)
    (h : allocFits base bpses 0) :
    sumPlan (buildPlan base bpses) = base := by
  unfold buildPlan
  have hsum := distribution_planAux_sums base bpses 0 0 h
  simpa using hsum

theorem distribution_plan_single (base b i : Nat) :
    buildPlanAux base [b] i 0 = [(i, base)] := rfl

def run (s : DistributionState) : Option DistributionState :=
  if s.status = DistributionStatus.paid then none
  else some { s with status := DistributionStatus.paid, nonce := s.nonce + 1 }

theorem distribution_run_once (s s' : DistributionState)
    (h : run s = some s') : run s' = none := by
  by_cases hp : s.status = DistributionStatus.paid
  · simp [run, hp] at h
  · simp [run, hp] at h
    subst s'
    simp [run]

theorem distribution_run_preserves_plan (s s' : DistributionState)
    (h : run s = some s') : s'.plan = s.plan := by
  by_cases hp : s.status = DistributionStatus.paid
  · simp [run, hp] at h
  · simp [run, hp] at h
    subst s'
    rfl

theorem distribution_run_sums (s s' : DistributionState) (base : Nat) (bpses : List Nat)
    (h : run s = some s') (hp : s.plan = buildPlan base bpses)
    (hfit : allocFits base bpses 0) :
    sumPlan s'.plan = base := by
  rw [distribution_run_preserves_plan s s' h, hp]
  exact distribution_plan_sums base bpses hfit

theorem distribution_plan_sound (s : DistributionState) (base : Nat) (bpses : List Nat)
    (hp : s.plan = buildPlan base bpses) (hfit : allocFits base bpses 0) :
    sumPlan s.plan = base := by
  rw [hp]
  exact distribution_plan_sums base bpses hfit

theorem distribution_run_sound (s s' : DistributionState)
    (h : run s = some s') :
    s'.status = DistributionStatus.paid ∧ s'.plan = s.plan
      ∧ s'.nonce = s.nonce + 1 := by
  by_cases hp : s.status = DistributionStatus.paid
  · simp [run, hp] at h
  · simp [run, hp] at h
    subst s'
    exact ⟨rfl, rfl, rfl⟩

theorem distribution_run_refuses (s : DistributionState)
    (h : s.status = DistributionStatus.paid) : run s = none := by
  simp [run, h]

def achievableDistribution : DistributionState where
  base := 1000
  plan := buildPlan 1000 [4000, 6000]
  status := DistributionStatus.planned
  nonce := 0

theorem distribution_reachable :
    ∃ s', run achievableDistribution = some s'
      ∧ s'.status = DistributionStatus.paid := by
  refine ⟨{ achievableDistribution with status := DistributionStatus.paid, nonce := 1 },
    ?_, rfl⟩
  simp [run, achievableDistribution]

end RSure.Model.Distribution
