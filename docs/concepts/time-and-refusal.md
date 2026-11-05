# Time, refusal and concurrency

> **Status:** Implemented (source + static/parser gates).

- All periods are block heights. There are no timers.
- Expiry is lazy: `Slip.expire` and `Policy.expire` are permissionless after the relevant
  height. A grant that is never consumed is released by `Syndicate.expireQuote`.
- Every mutating arm consumes its object's cell, validates the consumed snapshot, and reposts
  exactly once. Reads use a peek and are hints only.
- A deploy is atomic. Deploys do not interleave, so two settlement attempts are serialised by
  the policy cell and the claim's settled flag.
- A refusal returns `(false, reason)` before a value move. After a value move, an unexpected
  branch calls `1/0` and the deploy rolls back.
- Never use `select` for exclusivity; the node desugars it into parallel receives.
- `*x` sends a name, `@x` sends data. Purses, facets and tokens are names.
- A deploy lives for 50 blocks; anchor `validAfterBlockNumber` at the tip.
