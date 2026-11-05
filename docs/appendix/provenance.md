# Provenance and license

> **Status:** Stable.

r-sure is AGPL-3.0-only. It adapts patterns from the rhovision-org sibling repositories:

- r-share: the component-directory, consume-then-repost state discipline, owner-auth and
  r-cash adapter patterns, and the release-token idea used by `LineGrant`.
- r-gen: the `OracleFactory.open` / `applyDecision` adjudication protocol and the
  insurability tri-test.
- r-cash: accounts, issuer, purses and deposit facets as the settlement rail.

The NAIC/CIPR paper in `docs/papers/` is third-party background, not a source of the
contracts and not relicensed: Daniel R. Robles, "Insurance: The Highest and Best Use Case
for Blockchain Technology," NAIC CIPR Newsletter, July 2016, pp. 17–27. It is cited on
pp. 17, 20, 22 and 25 for the capital-cost, insurability and adjudication rationale. It is
an opinion column, not an NAIC standard or a specification; its views are the author's, not
the NAIC's. The design chapter is
[Design philosophy: the NAIC/CIPR basis](../primer/design-philosophy.md); the page-level
extract is [`../papers/extracts/robles2016naic.md`](../papers/extracts/robles2016naic.md).

This repository does not modify r-gen, r-cash or r-share.
