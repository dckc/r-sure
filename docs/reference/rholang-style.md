# Rholang match style

`match` is the strongest control-flow primitive in Rholang and the r-sure contracts use it
for every dispatch decision. The gate in `tools/check_match_style.py` keeps the use
effective: shallow, total where the state is held, and free of duplicated or dead arms.
It is wired into `make spec-check`, so a contract change that regresses the style fails CI.

## Measured semantics

- A `match` whose patterns do not match succeeds silently with **no continuation**. A
  receive that never matches and a match with no matching arm both leave the caller
  waiting.
- The **first** matching arm wins. Order is behaviour, not formatting.
- Tuple patterns have exact arity.
- `match x { y => P }` is the language's `let`; a single binder is not a dispatch.
- There are no or-patterns. A membership test is an `if` with `||`, or a tuple match on
  the case tags.
- `@` in a match pattern is a parse error. Name patterns are bare in match patterns and
  process patterns are `@name`.
- `<-` consumes the datum; `<<-` peeks it. A match that runs while a cell is consumed is
  a **mutating** match and owns the repost.
- `1/0` aborts the deploy; it is an accepted terminal for a refusal that must not continue.

## Rules

| ID | Gate | Rule |
|---|---|---|
| M-001 | yes | Non-let dispatch depth is at most 3. Nested non-let `match` and tag-dispatch `if` count; `contract` resets; `for`, `new`, guards, `else` and lets do not count. |
| M-002 | yes | No same-enum `else if`/`else { if }` ladder. One membership `if (x == "a" \|\| x == "b")` is allowed. |
| M-003 | yes | A mutating match has a total arm (`_`, a lone binder, a total tuple bind, or a boolean pair). |
| M-004 | yes | The total arm reposts the held cell and replies, aborts with `1/0`, or forwards the cell and reply to a helper that is itself checked. |
| M-005 | yes | No identical bodies across distinct patterns, no duplicate pattern, no catch-all before the last arm. |
| M-006 | yes | No single `_`/lone-binder arm whose body begins with a presence test on the same scrutinee. |
| M-007 | yes | Every `match` token parses; no token/parse drift. |
| M-008 | yes | No match without arms. |
| A-001 | advice | A map pattern should include `..._`; report only. |
| A-002 | advice | A class-membership list should not be duplicated across files; report only. |

## Good and bad shapes

Dispatch on a tag with a value arm and a named refusal:

```rho
match s.get("status") {
  "active" => { ret!((true, Nil)) }
  "suspended" => { ret!((false, "suspended")) }
  _ => { ret!((false, "status")) }
}
```

Mutating match: every terminal arm reposts the snapshot before replying.

```rho
for (@s <- state) {
  match s.get("covers").get(claimId) {
    Nil => { state!({...s, "covers": ...}) | ret!((true, Nil)) }
    _ => { state!(s) | ret!((false, "already covered")) }
  }
}
```

Bad: a wildcard arm followed by a presence test on the same scrutinee. The match is dead;
use `Nil` and a binder arm instead.

```rho
match l.get("paidFor").get(claimId) {
  _ => { if (l.get("paidFor").get(claimId) != Nil) { ... } else { ... } }
}
```

Bad: the refusal arm replies after the cell was consumed but never reposts it. The next
call on the instance blocks.

```rho
for (@s <- state) {
  match r {
    (true, value) => { ... }
    _ => { ret!((false, "unavailable")) }   // state lost
  }
}
```

Stage extraction keeps the depth at 3 or less. Helpers receive the snapshot as data and the
state cell as a name only to repost:

```rho
contract settleMath(@s, stateCell, @claimId, ret2) = {
  new mCh in {
    resolve!("component:suremath", *mCh) |
    for (@m <- mCh) {
      match m {
        (true, SureMath) => { settleCover!(s, SureMath, *stateCell, claimId, *ret2) }
        _ => { stateCell!(s) | ret2!((false, "math unavailable")) }
      }
    }
  }
}
```

## Do not force a match

The gate never asks for a match where a guard is clearer:

- range and arithmetic guards (`if (amount < 1 || amount > cap)`);
- linear-name identity (`if (*a != *b)`);
- membership lists (`if (x == "a" || x == "b")`);
- `1/0` abort terminals;
- index recursion over a list, where the list-pattern style is not yet possible.

Rholang has no or-patterns and no guard clauses on match arms, so expressing alternatives
as a single-arm match followed by an `if` is worse than the guard itself.

## Commands

```sh
make check-match-style          # self-test, then the hard gate
make check-match-style-report   # counts, depth histogram, per-file inventory, advice
python3 tools/check_match_style.py --self-test
python3 tools/check_match_style.py --json
```

A suppression is a comment `// match-style: allow M-00X reason` on the match line or the
line before it. It is for a demonstrated false positive only; the tree carries none.
