namespace RSure.Model.Boundary

/-! Externals that the Lean model does not prove. Each field mirrors an assumption in
    `spec/lean/claims.yaml`. Keeping them in one structure makes the boundary auditable. -/

structure Boundary where
  /-- An r-cash purse or issuer move conserves value or fails. ERTP is not modelled. -/
  ertpNativeTotal : Prop
  /-- r-gen `OracleCase.execute` calls the subject's `applyDecision` once, for the named case. -/
  rgenOracleBinding : Prop
  /-- Deployer identity and 2-of-3 signatures are unforgeable. -/
  cryptoAuthority : Prop
  /-- A failed deploy rolls back all state and value effects. -/
  deployAtomicity : Prop
  /-- Contract integer bounds hold; Lean `Nat` is unbounded. -/
  arithmeticNoOverflow : Prop
  /-- No liveness or fairness claim; the model proves safety only. -/
  schedulerFairness : Prop
  /-- The global pause gate is not a proved gate while F-003 is open. -/
  pauseGate : Prop
  /-- Evidence quality, not merely evidence presence, is an off-chain underwriting duty. -/
  evidenceQuality : Prop

/-- The boundary assumed by the component model. -/
def assumed : Boundary where
  ertpNativeTotal := True
  rgenOracleBinding := True
  cryptoAuthority := True
  deployAtomicity := True
  arithmeticNoOverflow := True
  schedulerFairness := True
  pauseGate := True
  evidenceQuality := True

end RSure.Model.Boundary
