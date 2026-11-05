# Node evidence snapshot

`deep_par_codec.rs` is a verbatim copy of the regression test added to the RNodeRust
checkout used for RCA-001 (rchain-community/rchain-rust at `e2d073dc`, plus the local
`wargame/arms-rig` commits). It is snapshotted here because the test does not exist in the
upstream commit CI checks out; the audit register must be able to resolve every evidence
reference from a clean checkout.

The other RCA evidence points at files that do exist upstream: `models/Cargo.toml` and
`models/src/wire.rs`. CI checks the node out under `RNodeRust/` in the workspace, and the
checkers accept either the sibling path used locally or the workspace path.
