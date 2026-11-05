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

end RSure.Model.Grant
