import RSure.Model.Types

namespace RSure.Model.Grant

open RSure.Model.Types

/-! A `LineGrant` is one-shot: an open grant can be consumed, revoked or expired exactly
    once, and a consumed grant cannot be consumed again. -/

structure GrantState where
  status : GrantStatus
  deriving DecidableEq, Repr

def consume (g : GrantState) (tokenOk idsOk : Bool) : Option GrantState :=
  if g.status = GrantStatus.open then
    if tokenOk then
      if idsOk then some { status := GrantStatus.consumed } else none
    else none
  else none

theorem grant_consume_moves (g : GrantState) (tokenOk idsOk : Bool) (g' : GrantState)
    (h : consume g tokenOk idsOk = some g') :
    g'.status = GrantStatus.consumed := by
  by_cases h1 : g.status = GrantStatus.open
  · by_cases h2 : tokenOk
    · by_cases h3 : idsOk
      · simp [consume, h1, h2, h3] at h
        subst g'
        rfl
      · simp [consume, h1, h2, h3] at h
    · simp [consume, h1, h2] at h
  · simp [consume, h1] at h

theorem grant_consume_once (g : GrantState) (tokenOk idsOk : Bool) (g' : GrantState)
    (h : consume g tokenOk idsOk = some g') :
    consume g' tokenOk idsOk = none := by
  have hm := grant_consume_moves g tokenOk idsOk g' h
  simp [consume, hm]

/-! CP-05 LineGrant. The deployed `LineGrant@"consume"` also binds the holder token and
    the quote terms (slip id, share and exposure). The record below carries those fields
    so the binding theorem is about the same guard the contract checks. -/

structure GrantRecord where
  status : GrantStatus
  slipId : Nat
  shareBps : Nat
  exposure : Nat
  expiryHeight : Nat
  deriving DecidableEq, Repr

def consumeBound (g : GrantRecord) (slipId shareBps exposure : Nat)
    (holderOk : Bool) : Option GrantRecord :=
  if g.status = GrantStatus.open then
    if holderOk then
      if slipId = g.slipId ∧ shareBps = g.shareBps ∧ exposure = g.exposure then
        some { g with status := GrantStatus.consumed }
      else none
    else none
  else none

def GrantWF (g : GrantRecord) : Prop :=
  g.status = GrantStatus.open → 0 < g.exposure ∧ 0 < g.shareBps

theorem grant_consume_sound (g g' : GrantRecord) (slipId shareBps exposure : Nat)
    (holderOk : Bool) (hwf : GrantWF g)
    (h : consumeBound g slipId shareBps exposure holderOk = some g') :
    GrantWF g' ∧ g'.status = GrantStatus.consumed
      ∧ g'.slipId = g.slipId ∧ g'.shareBps = g.shareBps
      ∧ g'.exposure = g.exposure := by
  by_cases ho : g.status = GrantStatus.open
  · by_cases hh : holderOk
    · by_cases hm : slipId = g.slipId ∧ shareBps = g.shareBps ∧ exposure = g.exposure
      · simp [consumeBound, ho, hh, hm] at h
        subst g'
        exact ⟨by intro hc; simp at hc, rfl, rfl, rfl, rfl⟩
      · simp [consumeBound, ho, hh, hm] at h
    · simp [consumeBound, ho, hh] at h
  · simp [consumeBound, ho] at h

theorem grant_binding (g g' : GrantRecord) (slipId shareBps exposure : Nat)
    (holderOk : Bool) (h : consumeBound g slipId shareBps exposure holderOk = some g') :
    slipId = g.slipId ∧ shareBps = g.shareBps ∧ exposure = g.exposure
      ∧ holderOk = true := by
  by_cases ho : g.status = GrantStatus.open
  · by_cases hh : holderOk
    · by_cases hm : slipId = g.slipId ∧ shareBps = g.shareBps ∧ exposure = g.exposure
      · exact ⟨hm.1, hm.2.1, hm.2.2, hh⟩
      · simp [consumeBound, ho, hh, hm] at h
    · simp [consumeBound, ho, hh] at h
  · simp [consumeBound, ho] at h

theorem grant_consume_status (g g' : GrantRecord) (slipId shareBps exposure : Nat)
    (holderOk : Bool) (h : consumeBound g slipId shareBps exposure holderOk = some g') :
    g'.status = GrantStatus.consumed := by
  by_cases ho : g.status = GrantStatus.open
  · by_cases hh : holderOk
    · by_cases hm : slipId = g.slipId ∧ shareBps = g.shareBps ∧ exposure = g.exposure
      · simp [consumeBound, ho, hh, hm] at h
        subst g'
        rfl
      · simp [consumeBound, ho, hh, hm] at h
    · simp [consumeBound, ho, hh] at h
  · simp [consumeBound, ho] at h

theorem grant_consume_once_bound (g g' : GrantRecord) (slipId shareBps exposure : Nat)
    (holderOk : Bool) (h : consumeBound g slipId shareBps exposure holderOk = some g') :
    consumeBound g' slipId shareBps exposure holderOk = none := by
  have hs := grant_consume_status g g' slipId shareBps exposure holderOk h
  simp [consumeBound, hs]

theorem grant_consume_refuses_closed (g : GrantRecord) (slipId shareBps exposure : Nat)
    (holderOk : Bool) (h : g.status ≠ GrantStatus.open) :
    consumeBound g slipId shareBps exposure holderOk = none := by
  simp [consumeBound, h]

theorem grant_consume_refuses_holder (g : GrantRecord) (slipId shareBps exposure : Nat)
    (h : holderOk = false) :
    consumeBound g slipId shareBps exposure holderOk = none := by
  by_cases ho : g.status = GrantStatus.open
  · simp [consumeBound, ho, h]
  · simp [consumeBound, ho]

theorem grant_consume_refuses_mismatch (g : GrantRecord) (slipId shareBps exposure : Nat)
    (holderOk : Bool)
    (h : ¬ (slipId = g.slipId ∧ shareBps = g.shareBps ∧ exposure = g.exposure)) :
    consumeBound g slipId shareBps exposure holderOk = none := by
  by_cases ho : g.status = GrantStatus.open
  · by_cases hh : holderOk
    · simp [consumeBound, ho, hh, h]
    · simp [consumeBound, ho, hh]
  · simp [consumeBound, ho]

def openGrant : GrantRecord where
  status := GrantStatus.open
  slipId := 7
  shareBps := 5000
  exposure := 100
  expiryHeight := 10

theorem grant_reachable :
    ∃ g', consumeBound openGrant 7 5000 100 true = some g'
      ∧ g'.status = GrantStatus.consumed := by
  refine ⟨{ openGrant with status := GrantStatus.consumed }, ?_, rfl⟩
  simp [consumeBound, openGrant]

end RSure.Model.Grant
