# Provenance and license

> **Status:** Stable.

r-sure is AGPL-3.0-only. It adapts patterns from the rhovision-org sibling repositories:

- r-share: the component-directory, consume-then-repost state discipline, owner-auth and
  r-cash adapter patterns, and the release-token idea used by `LineGrant`.
- r-gen: the `OracleFactory.open` / `applyDecision` adjudication protocol and the
  insurability tri-test.
- r-cash: accounts, issuer, purses and deposit facets as the settlement rail.

The NAIC/CIPR paper in `docs/papers/` is third-party background; it is not a source of the
contracts and is not relicensed.

This repository does not modify r-gen, r-cash or r-share.
