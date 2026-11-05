import RSure.Model.Types

namespace RSure.Model.Books

/-! Policy and claim books are append-only indexes: an id registers once and lookup returns
    the registered value. -/

structure Book where
  entries : List (Nat × Nat)
  deriving DecidableEq, Repr

def lookup (k : Nat) : List (Nat × Nat) → Option Nat
  | [] => none
  | (k', v) :: rest => if k = k' then some v else lookup k rest

def register (b : Book) (k v : Nat) : Option Book :=
  if lookup k b.entries = none then
    some { b with entries := (k, v) :: b.entries }
  else none

theorem book_register_absent (b b' : Book) (k v : Nat)
    (h : register b k v = some b') : lookup k b.entries = none := by
  by_cases hk : lookup k b.entries = none
  · exact hk
  · simp [register, hk] at h

theorem book_lookup_sound (b b' : Book) (k v : Nat)
    (h : register b k v = some b') : lookup k b'.entries = some v := by
  by_cases hk : lookup k b.entries = none
  · simp [register, hk] at h
    subst b'
    simp [lookup]
  · simp [register, hk] at h

theorem book_register_unique (b b' : Book) (k v v2 : Nat)
    (h : register b k v = some b') : register b' k v2 = none := by
  have hl := book_lookup_sound b b' k v h
  simp [register, hl]

theorem book_lookup_preserved (b b' : Book) (k v k' : Nat)
    (h : register b k v = some b') (hne : k ≠ k') :
    lookup k' b'.entries = lookup k' b.entries := by
  by_cases hk : lookup k b.entries = none
  · simp [register, hk] at h
    subst b'
    simp [lookup, hne, Ne.symm hne]
  · simp [register, hk] at h

end RSure.Model.Books
