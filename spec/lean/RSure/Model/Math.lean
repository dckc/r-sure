import RSure.Basic

namespace RSure.Model.Math

open RSure

/-! Premium split, payable and allocation, mirroring `contracts/src/deploy/04_math.rho`. -/

structure PremiumParts where
  commission : Nat
  levy : Nat
  net : Nat
  deriving DecidableEq, Repr

/-- Commission and central-fund levy are shares of the gross premium; the net premium
    absorbs the integer remainder. -/
def premiumSplit (total brokerBps fundBps : Nat) : PremiumParts :=
  let c := share total brokerBps
  let l := share total fundBps
  { commission := c, levy := l, net := total - c - l }

theorem math_premiumSplit_le (total brokerBps fundBps : Nat)
    (h : brokerBps + fundBps ≤ BPS) :
    (premiumSplit total brokerBps fundBps).commission
      + (premiumSplit total brokerBps fundBps).levy ≤ total := by
  dsimp [premiumSplit]
  calc
    share total brokerBps + share total fundBps ≤ share total (brokerBps + fundBps) :=
      share_add_le total brokerBps fundBps
    _ ≤ total := share_le_self h

theorem math_premiumSplit_conserves (total brokerBps fundBps : Nat)
    (h : brokerBps + fundBps ≤ BPS) :
    (premiumSplit total brokerBps fundBps).commission
      + (premiumSplit total brokerBps fundBps).levy
      + (premiumSplit total brokerBps fundBps).net = total := by
  have hle : share total brokerBps + share total fundBps ≤ total := by
    calc
      share total brokerBps + share total fundBps ≤ share total (brokerBps + fundBps) :=
        share_add_le total brokerBps fundBps
      _ ≤ total := share_le_self h
  change share total brokerBps + share total fundBps
    + (total - share total brokerBps - share total fundBps) = total
  omega

theorem math_premiumSplit_commission_le (total brokerBps fundBps : Nat)
    (h : brokerBps + fundBps ≤ BPS) :
    (premiumSplit total brokerBps fundBps).commission ≤ total := by
  have hb : brokerBps ≤ BPS := by omega
  simp only [premiumSplit]
  exact share_le_self hb

theorem math_premiumSplit_levy_le (total brokerBps fundBps : Nat)
    (h : brokerBps + fundBps ≤ BPS) :
    (premiumSplit total brokerBps fundBps).levy ≤ total := by
  have hb : fundBps ≤ BPS := by omega
  simp only [premiumSplit]
  exact share_le_self hb

/-- The contract's branch order: the agreed amount is capped by the aggregate only while it
    is below the per-claim limit; once it reaches the per-claim limit, that limit applies. -/
def payableBase (agreed perClaim aggregate : Nat) : Nat :=
  if agreed < perClaim then
    if agreed < aggregate then agreed else aggregate
  else perClaim

/-- Payable after the deductible. `Nat` subtraction truncates at zero. -/
def payable (agreed perClaim aggregate deductible : Nat) : Nat :=
  payableBase agreed perClaim aggregate - deductible

theorem math_payable_le_agreed (agreed perClaim aggregate deductible : Nat) :
    payable agreed perClaim aggregate deductible ≤ agreed := by
  unfold payable payableBase
  by_cases h1 : agreed < perClaim
  · simp [h1]
    by_cases h2 : agreed < aggregate
    · simp [h2]
    · simp [h2]
      exact Nat.le_trans (Nat.sub_le aggregate deductible) (Nat.le_of_not_lt h2)
  · simp [h1]
    exact Nat.le_trans (Nat.sub_le perClaim deductible) (Nat.le_of_not_lt h1)

theorem math_payable_le_perClaim (agreed perClaim aggregate deductible : Nat) :
    payable agreed perClaim aggregate deductible ≤ perClaim := by
  unfold payable payableBase
  by_cases h1 : agreed < perClaim
  · simp [h1]
    by_cases h2 : agreed < aggregate
    · simp [h2]
      exact Nat.le_trans (Nat.sub_le agreed deductible) (Nat.le_of_lt h1)
    · simp [h2]
      exact Nat.le_trans (Nat.sub_le aggregate deductible)
        (Nat.le_trans (Nat.le_of_not_lt h2) (Nat.le_of_lt h1))
  · simp [h1]

theorem math_payable_le_aggregate_of_lt (agreed perClaim aggregate deductible : Nat)
    (h1 : agreed < perClaim) :
    payable agreed perClaim aggregate deductible ≤ aggregate := by
  unfold payable payableBase
  simp [h1]
  by_cases h2 : agreed < aggregate
  · simp [h2]
    exact Nat.le_trans (Nat.sub_le agreed deductible) (Nat.le_of_lt h2)
  · simp [h2]

theorem math_payable_zero_of_le_deductible (agreed perClaim aggregate deductible : Nat)
    (h : payableBase agreed perClaim aggregate ≤ deductible) :
    payable agreed perClaim aggregate deductible = 0 := by
  unfold payable
  exact Nat.sub_eq_zero_of_le h

/-- Allocation with the last bucket absorbing the integer remainder. -/
def allocAux (amount : Nat) : List Nat → Nat → List Nat
  | [], _ => []
  | [_b], paid => [amount - paid]
  | b :: bs, paid => share amount b :: allocAux amount bs (paid + share amount b)

def alloc (amount : Nat) (bpses : List Nat) : List Nat :=
  allocAux amount bpses 0

/-- The contract's `paid == amount` feasibility condition, made structural. -/
def allocFits (amount : Nat) : List Nat → Nat → Prop
  | [], paid => paid = amount
  | [_b], paid => paid ≤ amount
  | b :: bs, paid =>
      paid + share amount b ≤ amount ∧ allocFits amount bs (paid + share amount b)

theorem math_allocAux_sums (amount : Nat) :
    ∀ (bpses : List Nat) (paid : Nat), allocFits amount bpses paid →
      sumNat (allocAux amount bpses paid) = amount - paid := by
  intro bpses
  induction bpses with
  | nil =>
      intro paid h
      simp [allocAux, sumNat, allocFits] at h ⊢
      omega
  | cons b bs ih =>
      intro paid h
      cases bs with
      | nil => simp [allocAux, sumNat]
      | cons c cs =>
          simp only [allocAux, allocFits, sumNat] at h ⊢
          rw [ih (paid + share amount b) h.2]
          omega

theorem math_alloc_sums (amount : Nat) (bpses : List Nat)
    (h : allocFits amount bpses 0) :
    sumNat (alloc amount bpses) = amount := by
  unfold alloc
  have hsum := math_allocAux_sums amount bpses 0 h
  simpa using hsum

theorem math_lineExposures_sums (aggregate : Nat) (bpses : List Nat)
    (h : allocFits aggregate bpses 0) :
    sumNat (alloc aggregate bpses) = aggregate :=
  math_alloc_sums aggregate bpses h

end RSure.Model.Math
