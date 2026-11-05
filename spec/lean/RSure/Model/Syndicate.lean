import RSure.Basic
import RSure.Model.Types

namespace RSure.Model.Syndicate

open RSure
open RSure.Model.Types

/-! Syndicate capital, quotes, lines and loss payments, mirroring `10_syndicate.rho`.
    `committed` is reserved by open quotes, `written` is bound line exposure net of paid
    losses, and free capacity is `capital - committed - written`. -/

structure SyndicateState where
  capital : Nat
  committed : Nat
  written : Nat
  premiums : Nat
  claimsPaid : Nat
  nonce : Nat
  status : SyndicateStatus
  deriving DecidableEq, Repr

def free (s : SyndicateState) : Nat := s.capital - s.committed - s.written

/-- A syndicate's promises never exceed its capital. -/
def SyndicateWF (s : SyndicateState) : Prop := s.committed + s.written ≤ s.capital

structure QuoteArgs where
  manager : Bool
  classOk : Bool
  shareBps : Nat
  exposure : Nat
  expiryHeight : Nat
  nowHeight : Nat
  deriving DecidableEq, Repr

def quote (s : SyndicateState) (a : QuoteArgs) : Option SyndicateState :=
  if a.manager then
    if s.status = SyndicateStatus.active then
      if a.classOk then
        if a.shareBps < 1 || a.shareBps > BPS || a.exposure < 1
            || a.expiryHeight ≤ a.nowHeight then none
        else if a.exposure > free s then none
        else some { s with committed := s.committed + a.exposure, nonce := s.nonce + 1 }
      else none
    else none
  else none

theorem synd_quote_WF (s s' : SyndicateState) (a : QuoteArgs)
    (hwf : SyndicateWF s) (h : quote s a = some s') :
    SyndicateWF s' ∧ s'.committed = s.committed + a.exposure
      ∧ s'.written = s.written ∧ free s' = free s - a.exposure := by
  by_cases hm : a.manager
  · by_cases hs : s.status = SyndicateStatus.active
    · by_cases hc : a.classOk
      · by_cases hb : a.shareBps < 1 || a.shareBps > BPS || a.exposure < 1
            || a.expiryHeight ≤ a.nowHeight
        · simp [quote, hm, hs, hc, hb] at h
        · by_cases hcap : a.exposure > free s
          · simp [quote, hm, hs, hc, hb, hcap] at h
          · simp [quote, hm, hs, hc, hb, hcap] at h
            subst s'
            have hcap' : a.exposure ≤ s.capital - s.committed - s.written := by
              unfold free at hcap
              omega
            refine ⟨?_, rfl, rfl, ?_⟩
            · change s.committed + a.exposure + s.written ≤ s.capital
              unfold SyndicateWF at hwf
              omega
            · change s.capital - (s.committed + a.exposure) - s.written
                = (s.capital - s.committed - s.written) - a.exposure
              unfold SyndicateWF at hwf
              omega
      · simp [quote, hm, hs, hc] at h
    · simp [quote, hm, hs] at h
  · simp [quote, hm] at h

theorem synd_quote_reserves (s s' : SyndicateState) (a : QuoteArgs)
    (hwf : SyndicateWF s) (h : quote s a = some s') :
    s'.committed = s.committed + a.exposure ∧ free s' = free s - a.exposure := by
  have hf := synd_quote_WF s s' a hwf h
  exact ⟨hf.2.1, hf.2.2.2⟩

theorem synd_quote_requires_capacity (s s' : SyndicateState) (a : QuoteArgs)
    (h : quote s a = some s') :
    a.exposure ≤ free s := by
  by_cases hm : a.manager
  · by_cases hs : s.status = SyndicateStatus.active
    · by_cases hc : a.classOk
      · by_cases hb : a.shareBps < 1 || a.shareBps > BPS || a.exposure < 1
            || a.expiryHeight ≤ a.nowHeight
        · simp [quote, hm, hs, hc, hb] at h
        · by_cases hcap : a.exposure > free s
          · simp [quote, hm, hs, hc, hb, hcap] at h
          · simp [quote, hm, hs, hc, hb, hcap] at h
            omega
      · simp [quote, hm, hs, hc] at h
    · simp [quote, hm, hs] at h
  · simp [quote, hm] at h

/-- A grant consumes one open quote and moves its exposure from committed to written. -/
def openLine (s : SyndicateState) (exposure : Nat) (grantOk : Bool) :
    Option SyndicateState :=
  if grantOk then
    if exposure < 1 || exposure > s.committed then none
    else
      some { s with
        committed := s.committed - exposure
        written := s.written + exposure
        nonce := s.nonce + 1 }
  else none

theorem synd_openLine_WF (s s' : SyndicateState) (exposure : Nat) (grantOk : Bool)
    (hwf : SyndicateWF s) (h : openLine s exposure grantOk = some s') :
    SyndicateWF s' ∧ s'.committed = s.committed - exposure
      ∧ s'.written = s.written + exposure ∧ free s' = free s := by
  by_cases hg : grantOk
  · by_cases hb : exposure < 1 || exposure > s.committed
    · simp [openLine, hg, hb] at h
    · simp [openLine, hg, hb] at h
      subst s'
      have hb' : exposure ≤ s.committed := by
        have hb0 := hb
        simp only [Bool.or_eq_true, decide_eq_true_eq, not_or] at hb0
        omega
      refine ⟨?_, rfl, rfl, ?_⟩
      · change (s.committed - exposure) + (s.written + exposure) ≤ s.capital
        unfold SyndicateWF at hwf
        omega
      · change s.capital - (s.committed - exposure) - (s.written + exposure)
          = s.capital - s.committed - s.written
        unfold SyndicateWF at hwf
        omega
  · simp [openLine, hg] at h

theorem synd_openLine_moves (s s' : SyndicateState) (exposure : Nat) (grantOk : Bool)
    (hwf : SyndicateWF s) (h : openLine s exposure grantOk = some s') :
    s'.committed = s.committed - exposure ∧ s'.written = s.written + exposure := by
  have hf := synd_openLine_WF s s' exposure grantOk hwf h
  exact ⟨hf.2.1, hf.2.2.1⟩

/-- Release returns the unpaid exposure to free capacity. -/
def release (s : SyndicateState) (exposure paid : Nat) : Option SyndicateState :=
  if paid > exposure then none
  else if exposure - paid > s.written then none
  else
    some { s with
      written := s.written - (exposure - paid)
      nonce := s.nonce + 1 }

theorem synd_release_restores (s s' : SyndicateState) (exposure paid : Nat)
    (hwf : SyndicateWF s) (h : release s exposure paid = some s') :
    SyndicateWF s' ∧ s'.written = s.written - (exposure - paid)
      ∧ free s' = free s + (exposure - paid) := by
  by_cases hp : paid > exposure
  · simp [release, hp] at h
  · by_cases hw : exposure - paid > s.written
    · simp [release, hp, hw] at h
    · simp [release, hp, hw] at h
      subst s'
      refine ⟨?_, rfl, ?_⟩
      · change s.committed + (s.written - (exposure - paid)) ≤ s.capital
        unfold SyndicateWF at hwf
        omega
      · change s.capital - s.committed - (s.written - (exposure - paid))
          = (s.capital - s.committed - s.written) + (exposure - paid)
        unfold SyndicateWF at hwf
        omega

/-- A loss payment reduces capital and written exposure by the same amount. -/
def payLoss (s : SyndicateState) (amount : Nat) : Option SyndicateState :=
  if amount < 1 then none
  else if amount > s.written || amount > s.capital then none
  else
    some { s with
      capital := s.capital - amount
      written := s.written - amount
      claimsPaid := s.claimsPaid + amount
      nonce := s.nonce + 1 }

theorem synd_payLoss_preserves_free (s s' : SyndicateState) (amount : Nat)
    (hwf : SyndicateWF s) (h : payLoss s amount = some s') :
    SyndicateWF s' ∧ free s' = free s := by
  by_cases ha : amount < 1
  · simp [payLoss, ha] at h
  · by_cases hb : amount > s.written || amount > s.capital
    · simp [payLoss, ha, hb] at h
    · simp [payLoss, ha, hb] at h
      subst s'
      have hb' : amount ≤ s.written ∧ amount ≤ s.capital := by
        have hb0 := hb
        simp only [Bool.or_eq_true, decide_eq_true_eq, not_or] at hb0
        constructor <;> omega
      rcases hb' with ⟨hw, hc⟩
      refine ⟨?_, ?_⟩
      · change s.committed + (s.written - amount) ≤ s.capital - amount
        unfold SyndicateWF at hwf
        omega
      · change (s.capital - amount) - s.committed - (s.written - amount)
          = s.capital - s.committed - s.written
        omega

theorem synd_written_le_capital (s : SyndicateState) (h : SyndicateWF s) :
    s.written ≤ s.capital := by
  unfold SyndicateWF at h
  omega

theorem synd_capacity_invariant (s s' : SyndicateState) (a : QuoteArgs)
    (hwf : SyndicateWF s) (h : quote s a = some s') : SyndicateWF s' :=
  (synd_quote_WF s s' a hwf h).1

end RSure.Model.Syndicate
