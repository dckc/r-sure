import RSure.Basic
import RSure.Model.Types

namespace RSure.Model.Slip

open RSure
open RSure.Model.Types

/-! Placing-slip subscription and funding, mirroring `13_slip.rho`. A slip binds only when
    the insured has accepted, the premium is fully funded and subscriptions sum to 10000 bps.
    The model keeps share rates, not syndicate URIs. -/

structure SlipState where
  premiumTotal : Nat
  funded : Nat
  shares : List Nat
  insured : Nat
  insuredAccepted : Bool
  status : SlipStatus
  nonce : Nat
  deriving DecidableEq, Repr

/-- Acceptance is owner-gated and only allowed before binding. -/
def accept (s : SlipState) (who : Nat) : Option SlipState :=
  if who ≠ s.insured then none
  else if s.status ≠ SlipStatus.open ∧ s.status ≠ SlipStatus.subscribed then none
  else some { s with insuredAccepted := true, nonce := s.nonce + 1 }

/-- Subscription appends one syndicate's share rate. The share is bounded, and the
    syndicate must have issued a grant accepting the subscription. -/
def subscribe (s : SlipState) (shareBps : Nat) (grantOk : Bool) : Option SlipState :=
  if s.status ≠ SlipStatus.open ∧ s.status ≠ SlipStatus.subscribed then none
  else if shareBps < 1 || shareBps > BPS then none
  else if grantOk = false then none
  else some { s with shares := s.shares ++ [shareBps], nonce := s.nonce + 1 }

/-- The insured funds the premium. The model records the deposit locally; the ERTP move
    is the `ertp.native_total` boundary. -/
def fundPremium (s : SlipState) (who amount : Nat) : Option (SlipState × Nat) :=
  if who ≠ s.insured then none
  else if amount < 1 then none
  else some ({ s with funded := s.funded + amount, nonce := s.nonce + 1 }, amount)

/-- A bound slip is fully accepted, fully funded, non-empty and subscribed to 10000 bps. -/
def SlipWF (s : SlipState) : Prop :=
  s.status = SlipStatus.bound →
    s.insuredAccepted = true
      ∧ s.funded = s.premiumTotal
      ∧ s.shares ≠ []
      ∧ sumNat s.shares = BPS

theorem slip_accept_sound (s s' : SlipState) (who : Nat) (hwf : SlipWF s)
    (h : accept s who = some s') :
    SlipWF s' ∧ s'.insuredAccepted = true ∧ s'.shares = s.shares
      ∧ s'.funded = s.funded := by
  by_cases hw : who ≠ s.insured
  · simp [accept, hw] at h
  · by_cases hs : s.status ≠ SlipStatus.open ∧ s.status ≠ SlipStatus.subscribed
    · simp [accept, hw, hs] at h
    · simp [accept, hw, hs] at h
      subst s'
      refine ⟨?_, rfl, rfl, rfl⟩
      intro hb
      have hbnd : s.status = SlipStatus.bound := by simpa using hb
      exfalso
      exact hs ⟨by simp [hbnd], by simp [hbnd]⟩

theorem slip_subscribe_sound (s s' : SlipState) (shareBps : Nat) (grantOk : Bool)
    (hwf : SlipWF s) (h : subscribe s shareBps grantOk = some s') :
    SlipWF s' ∧ s'.shares = s.shares ++ [shareBps] ∧ s'.funded = s.funded := by
  by_cases hs : s.status ≠ SlipStatus.open ∧ s.status ≠ SlipStatus.subscribed
  · simp [subscribe, hs] at h
  · by_cases hb : shareBps < 1 || shareBps > BPS
    · simp [subscribe, hs, hb] at h
    · by_cases hg : grantOk = false
      · simp [subscribe, hs, hb, hg] at h
      · simp [subscribe, hs, hb, hg] at h
        subst s'
        refine ⟨?_, rfl, rfl⟩
        intro hbind
        have hbnd : s.status = SlipStatus.bound := by simpa using hbind
        exfalso
        exact hs ⟨by simp [hbnd], by simp [hbnd]⟩

theorem slip_fund_sound (s s' : SlipState) (who amount paid : Nat) (hwf : SlipWF s)
    (h : fundPremium s who amount = some (s', paid)) :
    paid = amount ∧ s'.funded = s.funded + amount ∧ s'.shares = s.shares
      ∧ s'.insuredAccepted = s.insuredAccepted := by
  by_cases hw : who ≠ s.insured
  · simp [fundPremium, hw] at h
  · by_cases ha : amount < 1
    · simp [fundPremium, hw, ha] at h
    · simp [fundPremium, hw, ha] at h
      rcases h with ⟨rfl, rfl⟩
      exact ⟨rfl, rfl, rfl, rfl⟩

theorem slip_accept_refuses_owner (s : SlipState) (who : Nat) (h : who ≠ s.insured) :
    accept s who = none := by
  simp [accept, h]

theorem slip_subscribe_refuses_share (s : SlipState) (shareBps : Nat) (grantOk : Bool)
    (h : shareBps < 1 ∨ shareBps > BPS) :
    subscribe s shareBps grantOk = none := by
  by_cases hs : s.status ≠ SlipStatus.open ∧ s.status ≠ SlipStatus.subscribed
  · simp [subscribe, hs]
  · have hb : (shareBps < 1 || shareBps > BPS) = true := by
      rcases h with h | h
      · simp [h]
      · simp [h]
    simp [subscribe, hs, hb]

theorem slip_fund_refuses_owner (s : SlipState) (who amount : Nat)
    (h : who ≠ s.insured) : fundPremium s who amount = none := by
  simp [fundPremium, h]

theorem slip_fund_refuses_amount (s : SlipState) (who amount : Nat)
    (h : amount < 1) : fundPremium s who amount = none := by
  by_cases hw : who ≠ s.insured
  · simp [fundPremium, hw]
  · simp [fundPremium, hw, h]

def bind (s : SlipState) : Option SlipState :=
  if s.insuredAccepted then
    if s.funded = s.premiumTotal then
      if s.shares = [] then none
      else if sumNat s.shares = BPS then
        some { s with status := SlipStatus.bound, nonce := s.nonce + 1 }
      else none
    else none
  else none

theorem slip_bind_requires_subscription (s s' : SlipState) (h : bind s = some s') :
    s.insuredAccepted = true ∧ s.funded = s.premiumTotal
      ∧ s.shares ≠ [] ∧ sumNat s.shares = BPS := by
  by_cases ha : s.insuredAccepted
  · by_cases hf : s.funded = s.premiumTotal
    · by_cases he : s.shares = []
      · simp [bind, ha, hf, he] at h
      · by_cases hb : sumNat s.shares = BPS
        · exact ⟨ha, hf, he, hb⟩
        · simp [bind, ha, hf, he, hb] at h
    · simp [bind, ha, hf] at h
  · simp [bind, ha] at h

theorem slip_share_sum_bps (s s' : SlipState) (h : bind s = some s') :
    sumNat s.shares = BPS :=
  (slip_bind_requires_subscription s s' h).2.2.2

theorem slip_bind_moves (s s' : SlipState) (h : bind s = some s') :
    s'.status = SlipStatus.bound ∧ s'.funded = s.funded := by
  by_cases ha : s.insuredAccepted
  · by_cases hf : s.funded = s.premiumTotal
    · by_cases he : s.shares = []
      · simp [bind, ha, hf, he] at h
      · by_cases hb : sumNat s.shares = BPS
        · simp [bind, ha, hf, he, hb] at h
          subst s'
          exact ⟨rfl, hf.symm⟩
        · simp [bind, ha, hf, he, hb] at h
    · simp [bind, ha, hf] at h
  · simp [bind, ha] at h

def expire (s : SlipState) (nowPast : Bool) : Option (SlipState × Nat) :=
  if nowPast then
    if s.status = SlipStatus.bound then none
    else
      some ({ s with status := SlipStatus.expired, nonce := s.nonce + 1 }, s.funded)
  else none

theorem slip_expire_refund (s s' : SlipState) (credit : Nat) (nowPast : Bool)
    (h : expire s nowPast = some (s', credit)) :
    credit = s.funded := by
  by_cases hn : nowPast
  · by_cases hb : s.status = SlipStatus.bound
    · simp [expire, hn, hb] at h
    · simp [expire, hn, hb] at h
      rcases h with ⟨rfl, rfl⟩
      rfl
  · simp [expire, hn] at h

theorem slip_expire_sound (s s' : SlipState) (credit : Nat) (nowPast : Bool)
    (hwf : SlipWF s) (h : expire s nowPast = some (s', credit)) :
    credit = s.funded ∧ s'.funded = s.funded ∧ s'.shares = s.shares := by
  by_cases hn : nowPast
  · by_cases hb : s.status = SlipStatus.bound
    · simp [expire, hn, hb] at h
    · simp [expire, hn, hb] at h
      rcases h with ⟨rfl, rfl⟩
      exact ⟨rfl, rfl, rfl⟩
  · simp [expire, hn] at h

theorem slip_expire_refuses_bound (s : SlipState) (nowPast : Bool)
    (h : s.status = SlipStatus.bound) : expire s nowPast = none := by
  by_cases hn : nowPast
  · simp [expire, hn, h]
  · simp [expire, hn]

theorem slip_bind_fields (s s' : SlipState) (h : bind s = some s') :
    s'.status = SlipStatus.bound
      ∧ s'.funded = s.funded
      ∧ s'.shares = s.shares
      ∧ s'.insuredAccepted = s.insuredAccepted
      ∧ s'.premiumTotal = s.premiumTotal := by
  by_cases ha : s.insuredAccepted
  · by_cases hf : s.funded = s.premiumTotal
    · by_cases he : s.shares = []
      · simp [bind, ha, hf, he] at h
      · by_cases hb : sumNat s.shares = BPS
        · simp [bind, ha, hf, he, hb] at h
          subst s'
          exact ⟨rfl, hf.symm, rfl, ha.symm, rfl⟩
        · simp [bind, ha, hf, he, hb] at h
    · simp [bind, ha, hf] at h
  · simp [bind, ha] at h

theorem slip_bind_sound (s s' : SlipState) (h : bind s = some s') :
    SlipWF s' ∧ s'.status = SlipStatus.bound ∧ s'.funded = s.funded := by
  have hb := slip_bind_requires_subscription s s' h
  have hf := slip_bind_fields s s' h
  refine ⟨?_, hf.1, hf.2.1⟩
  intro hbound
  refine ⟨?_, ?_, ?_, ?_⟩
  · rw [hf.2.2.2.1]; exact hb.1
  · rw [hf.2.1, hf.2.2.2.2]; exact hb.2.1
  · rw [hf.2.2.1]; exact hb.2.2.1
  · rw [hf.2.2.1]; exact hb.2.2.2

theorem slip_bind_refuses_unaccepted (s : SlipState)
    (h : s.insuredAccepted = false) : bind s = none := by
  simp [bind, h]

theorem slip_bind_refuses_funding (s : SlipState)
    (h : s.funded ≠ s.premiumTotal) : bind s = none := by
  by_cases hf : s.funded = s.premiumTotal
  · exact False.elim (h hf)
  · simp [bind, hf]

theorem slip_bind_refuses_empty (s : SlipState) (h : s.shares = []) :
    bind s = none := by
  by_cases ha : s.insuredAccepted
  · by_cases hf : s.funded = s.premiumTotal
    · simp [bind, ha, hf, h]
    · simp [bind, ha, hf]
  · simp [bind, ha]

theorem slip_bind_refuses_shares (s : SlipState) (h : sumNat s.shares ≠ BPS) :
    bind s = none := by
  by_cases ha : s.insuredAccepted
  · by_cases hf : s.funded = s.premiumTotal
    · by_cases he : s.shares = []
      · simp [bind, ha, hf, he]
      · simp [bind, ha, hf, he, h]
    · simp [bind, ha, hf]
  · simp [bind, ha]

def fundableSlip : SlipState where
  premiumTotal := 100
  funded := 0
  shares := [5000, 5000]
  insured := 1
  insuredAccepted := true
  status := SlipStatus.subscribed
  nonce := 0

def boundSlip : SlipState :=
  { fundableSlip with funded := 100, status := SlipStatus.bound, nonce := 1 }

theorem slip_reachable :
    ∃ s', bind boundSlip = some s' ∧ s'.status = SlipStatus.bound := by
  refine ⟨{ boundSlip with nonce := 2 }, ?_, rfl⟩
  simp [bind, boundSlip, fundableSlip, sumNat, BPS]

theorem slip_fund_reachable :
    ∃ s' paid, fundPremium fundableSlip 1 100 = some (s', paid)
      ∧ paid = 100 := by
  refine ⟨{ fundableSlip with funded := 100, nonce := 1 }, 100, ?_, rfl⟩
  simp [fundPremium, fundableSlip]

end RSure.Model.Slip
