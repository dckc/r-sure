# Audit charter

r-sure is a devnet-only research prototype. The audit is an internal, adversarial review of:

1. capacity and subscription integrity;
2. premium custody and distribution;
3. claim classification, agreement and settlement;
4. the optional r-gen evidence and adjudication path;
5. the r-cash payment boundary;
6. authority, replay and liveness.

Out of scope: regulatory compliance, KYC/AML, fiat custody, mainnet deployment, real value,
r-gen internals, r-cash internals, and the Rust/web scaffolds until they are implemented.

No finding is "fixed" unless the change and its regression test are in the tree and recorded
in `registers/findings.yaml`.
