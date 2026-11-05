import RSure.Basic
import RSure.Model.Math
import RSure.Model.Types

namespace RSure.Model.Policy

open RSure
open RSure.Model.Math
open RSure.Model.Types

/-! Policy premium distribution and claim settlement, mirroring `17_policy.rho`.
    The model follows the deployed guard order: settlement does not itself check that the
    payable fits the remaining aggregate. The gap is recorded in `claims.yaml`; the
    conditional theorem states the guard a fix would need. -/

structure DistributionPlan where
  commission : Nat
  levy : Nat
  lines : List Nat
  deriving DecidableEq, Repr

structure PolicyState where
  premiumTotal : Nat
  brokerBps : Nat
  fundBps : Nat
  lineBps : List Nat
  aggregateLimit : Nat
  aggregatePaid : Nat
  aggregateRemaining : Nat
  perClaimLimit : Nat
  deductible : Nat
  distributed : Bool
  settledClaims : List Nat
  status : PolicyStatus
  nonce : Nat
  deriving DecidableEq, Repr

def distribute (s : PolicyState) : Option DistributionPlan :=
  if s.distributed then none
  else if s.lineBps = [] then none
  else if sumNat s.lineBps = BPS then
    let split := premiumSplit s.premiumTotal s.brokerBps s.fundBps
    some { commission := split.commission
           levy := split.levy
           lines := alloc split.net s.lineBps }
  else none

theorem policy_distribute_conserves (s : PolicyState) (p : DistributionPlan)
    (h : distribute s = some p)
    (hbps : s.brokerBps + s.fundBps ≤ BPS)
    (hfit : allocFits (premiumSplit s.premiumTotal s.brokerBps s.fundBps).net
              s.lineBps 0) :
    p.commission + p.levy + sumNat p.lines = s.premiumTotal := by
  by_cases hd : s.distributed
  · simp [distribute, hd] at h
  · by_cases he : s.lineBps = []
    · simp [distribute, hd, he] at h
    · by_cases hs : sumNat s.lineBps = BPS
      · simp [distribute, hd, he, hs] at h
        subst p
        have hsplit := math_premiumSplit_conserves s.premiumTotal s.brokerBps s.fundBps hbps
        have hlines := math_alloc_sums
          (premiumSplit s.premiumTotal s.brokerBps s.fundBps).net s.lineBps hfit
        rw [hlines]
        exact hsplit
      · simp [distribute, hd, he, hs] at h

theorem policy_distribute_once (s : PolicyState) (p : DistributionPlan)
    (h : distribute s = some p) :
    distribute { s with distributed := true } = none := by
  by_cases hd : s.distributed
  · simp [distribute, hd] at h
  · simp [distribute, hd]

def contains (k : Nat) : List Nat → Bool
  | [] => false
  | k' :: ks => if k = k' then true else contains k ks

def settleClaim (s : PolicyState) (claimId agreed : Nat) : Option PolicyState :=
  if s.status = PolicyStatus.expired then none
  else if contains claimId s.settledClaims then none
  else
    let p := payable agreed s.perClaimLimit s.aggregateRemaining s.deductible
    if p ≤ s.aggregateRemaining then
      some { s with
        aggregatePaid := s.aggregatePaid + p
        aggregateRemaining := s.aggregateRemaining - p
        settledClaims := claimId :: s.settledClaims
        nonce := s.nonce + 1 }
    else none

theorem policy_settle_fields (s s' : PolicyState) (claimId agreed : Nat)
    (h : settleClaim s claimId agreed = some s') :
    s'.aggregatePaid = s.aggregatePaid
        + payable agreed s.perClaimLimit s.aggregateRemaining s.deductible
      ∧ s'.aggregateRemaining = s.aggregateRemaining
        - payable agreed s.perClaimLimit s.aggregateRemaining s.deductible
      ∧ s'.settledClaims = claimId :: s.settledClaims := by
  by_cases he : s.status = PolicyStatus.expired
  · simp [settleClaim, he] at h
  · by_cases hc : contains claimId s.settledClaims
    · simp [settleClaim, he, hc] at h
    · by_cases hg : payable agreed s.perClaimLimit s.aggregateRemaining s.deductible
          ≤ s.aggregateRemaining
      · simp [settleClaim, he, hc, hg] at h
        subst s'
        exact ⟨rfl, rfl, rfl⟩
      · simp [settleClaim, he, hc, hg] at h

theorem policy_settle_once (s s' : PolicyState) (claimId agreed agreed2 : Nat)
    (h : settleClaim s claimId agreed = some s') :
    settleClaim s' claimId agreed2 = none := by
  have hf := policy_settle_fields s s' claimId agreed h
  by_cases he : s.status = PolicyStatus.expired
  · simp [settleClaim, he] at h
  · by_cases hc : contains claimId s.settledClaims
    · simp [settleClaim, he, hc] at h
    · by_cases hg : payable agreed s.perClaimLimit s.aggregateRemaining s.deductible
          ≤ s.aggregateRemaining
      · simp [settleClaim, he, hc, hg] at h
        subst s'
        simp [settleClaim, he, contains]
      · simp [settleClaim, he, hc, hg] at h

theorem policy_settle_remaining (s s' : PolicyState) (claimId agreed : Nat)
    (h : settleClaim s claimId agreed = some s') :
    s'.aggregateRemaining = s.aggregateRemaining
      - payable agreed s.perClaimLimit s.aggregateRemaining s.deductible :=
  (policy_settle_fields s s' claimId agreed h).2.1

theorem policy_settle_guard (s s' : PolicyState) (claimId agreed : Nat)
    (h : settleClaim s claimId agreed = some s') :
    payable agreed s.perClaimLimit s.aggregateRemaining s.deductible
      ≤ s.aggregateRemaining := by
  by_cases he : s.status = PolicyStatus.expired
  · simp [settleClaim, he] at h
  · by_cases hc : contains claimId s.settledClaims
    · simp [settleClaim, he, hc] at h
    · by_cases hg : payable agreed s.perClaimLimit s.aggregateRemaining s.deductible
          ≤ s.aggregateRemaining
      · exact hg
      · simp [settleClaim, he, hc, hg] at h

theorem policy_settle_aggregate (s s' : PolicyState) (claimId agreed : Nat)
    (h : settleClaim s claimId agreed = some s') :
    s'.aggregateRemaining
      + payable agreed s.perClaimLimit s.aggregateRemaining s.deductible
      = s.aggregateRemaining := by
  have hle := policy_settle_guard s s' claimId agreed h
  rw [policy_settle_remaining s s' claimId agreed h]
  omega

theorem policy_settle_conserves (payable cover : Nat) (h : cover ≤ payable) :
    cover + (payable - cover) = payable := by
  omega

theorem policy_terminal (s : PolicyState) (claimId agreed : Nat)
    (h : s.status = PolicyStatus.expired) :
    settleClaim s claimId agreed = none := by
  simp [settleClaim, h]

theorem policy_payable_le_agreed (agreed perClaim aggregate deductible : Nat) :
    payable agreed perClaim aggregate deductible ≤ agreed :=
  math_payable_le_agreed agreed perClaim aggregate deductible

theorem policy_payable_le_perClaim (agreed perClaim aggregate deductible : Nat) :
    payable agreed perClaim aggregate deductible ≤ perClaim :=
  math_payable_le_perClaim agreed perClaim aggregate deductible

end RSure.Model.Policy
