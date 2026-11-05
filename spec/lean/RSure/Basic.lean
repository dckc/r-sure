namespace RSure

/-- Basis-point denominator. -/
def BPS : Nat := 10000

/-- Integer share of `amount` at `bps` basis points. -/
def share (amount bps : Nat) : Nat := amount * bps / BPS

theorem share_zero (amount : Nat) : share amount 0 = 0 := by
  simp [share]

theorem share_bps_zero (amount : Nat) : share amount BPS = amount := by
  unfold share BPS
  rw [Nat.mul_comm, Nat.mul_div_right _ (by decide : 0 < 10000)]

end RSure
