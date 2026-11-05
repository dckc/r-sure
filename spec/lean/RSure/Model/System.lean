import RSure.Basic
import RSure.Model.Math

namespace RSure.Model.System

open RSure
open RSure.Model.Math

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

end RSure.Model.System
