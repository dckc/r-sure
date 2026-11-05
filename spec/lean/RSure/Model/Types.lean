namespace RSure.Model.Types

/-! Shared status values. The model uses small inductives instead of Rholang strings so
    terminal-state claims can be stated as equations between constructors. -/

inductive SyndicateStatus where
  | active
  | suspended
  deriving DecidableEq, Repr

inductive GrantStatus where
  | open
  | consumed
  | revoked
  | expired
  deriving DecidableEq, Repr

inductive LineStatus where
  | bound
  | released
  deriving DecidableEq, Repr

inductive SlipStatus where
  | open
  | subscribed
  | bound
  | expired
  deriving DecidableEq, Repr

inductive DistributionStatus where
  | planned
  | paid
  deriving DecidableEq, Repr

inductive ClaimStatus where
  | notified
  | classified
  | assessed
  | assessing
  | agreed
  | disputed
  | upheld
  | partiallyUpheld
  | denied
  | settled
  | closed
  deriving DecidableEq, Repr

inductive PolicyStatus where
  | active
  | expired
  deriving DecidableEq, Repr

def ClaimStatus.terminal : ClaimStatus → Bool
  | .settled => true
  | .denied => true
  | .closed => true
  | _ => false

def PolicyStatus.terminal : PolicyStatus → Bool
  | .expired => true
  | .active => false

end RSure.Model.Types
