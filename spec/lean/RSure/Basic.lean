namespace RSure

/-- Basis-point denominator. -/
def BPS : Nat := 10000

/-- Integer share of `amount` at `bps` basis points, rounded down. -/
def share (amount bps : Nat) : Nat := amount * bps / BPS

/-- Sum of a list of natural numbers. -/
def sumNat : List Nat → Nat
  | [] => 0
  | x :: xs => x + sumNat xs

theorem share_zero (amount : Nat) : share amount 0 = 0 := by
  simp [share]

theorem share_bps_zero (amount : Nat) : share amount BPS = amount := by
  unfold share BPS
  rw [Nat.mul_comm, Nat.mul_div_right _ (by decide : 0 < 10000)]

/-- Floor division is superadditive. -/
theorem div_add_div_le (x y k : Nat) (hk : 0 < k) :
    x / k + y / k ≤ (x + y) / k := by
  rw [Nat.le_div_iff_mul_le hk, Nat.add_mul]
  exact Nat.add_le_add (Nat.div_mul_le_self x k) (Nat.div_mul_le_self y k)

/-- Splitting a basis-point rate across two shares cannot exceed one share at the sum. -/
theorem share_add_le (amount a b : Nat) :
    share amount a + share amount b ≤ share amount (a + b) := by
  unfold share
  rw [Nat.mul_add]
  exact div_add_div_le (amount * a) (amount * b) BPS (by decide)

/-- A share at or below 10000 bps never exceeds the amount. -/
theorem share_le_self {amount bps : Nat} (h : bps ≤ BPS) : share amount bps ≤ amount := by
  unfold share
  apply Nat.div_le_of_le_mul
  calc
    amount * bps ≤ amount * BPS := Nat.mul_le_mul_left amount h
    _ = BPS * amount := Nat.mul_comm _ _

/-- Sum of shares never exceeds the share of the summed rates. -/
theorem share_sum_le (amount : Nat) :
    ∀ bpses : List Nat,
      sumNat (bpses.map (fun b => share amount b)) ≤ share amount (sumNat bpses)
  | [] => by simp [sumNat]
  | b :: bs => by
      simp only [List.map_cons, sumNat]
      calc
        share amount b + sumNat (bs.map (fun b => share amount b))
            ≤ share amount b + share amount (sumNat bs) :=
              Nat.add_le_add_left (share_sum_le amount bs) _
        _ ≤ share amount (b + sumNat bs) := share_add_le amount b (sumNat bs)

/-- If the rates sum to at most 10000 bps, the shares sum to at most the amount. -/
theorem share_sum_le_self (amount : Nat) (bpses : List Nat)
    (h : sumNat bpses ≤ BPS) :
    sumNat (bpses.map (fun b => share amount b)) ≤ amount := by
  calc
    sumNat (bpses.map (fun b => share amount b)) ≤ share amount (sumNat bpses) :=
      share_sum_le amount bpses
    _ ≤ amount := share_le_self h

theorem sumNat_append (xs ys : List Nat) :
    sumNat (xs ++ ys) = sumNat xs + sumNat ys := by
  induction xs with
  | nil => simp [sumNat]
  | cons x xs ih => simp [sumNat, ih, Nat.add_assoc]

end RSure
