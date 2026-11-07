"""Heuristic Rholang `match` scanner for the match-style audit.

This is not a parser. It masks comments, strings and backtick URIs, finds `match` and
`if` blocks at brace level, extracts arms and scrutinees, and records the information the
style gate needs: dispatch depth, whether a match is a let, whether it is mutating, whether
it has a total arm, and whether its arms are identical or dead.

The depth model follows the audit contract:

* a `contract` frame resets dispatch depth;
* a non-let `match` and a tag-dispatch `if` each add one level;
* `for`, `new`, guards, `else` and arm/map/other braces add none.

Adapted in spirit from r-gen's `tools/rholang_control_flow.py` (same scanner approach), but
this version parses multi-line arms and distinguishes lets, tree depth and mutating state.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT_ROOT = ROOT / "contracts" / "src"
COMPONENTS = ROOT / "contracts" / "components.json"

MATCH_RE = re.compile(r"\bmatch\b")
IF_RE = re.compile(r"\bif\s*\(")
CONTRACT_RE = re.compile(r"\bcontract\s+[A-Za-z_][A-Za-z0-9_']*\s*\(")
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*$")
KEYWORDS = {"true", "false", "Nil", "match", "if", "else", "for", "new", "contract"}
REPLY_RE = re.compile(r"\b(?:ret\d*|deployId)!\s*\(")
ABORT_RE = re.compile(r"\b1\s*/\s*0\b")
STATE_SEND_TMPL = r"(?:@|\*)?\b{}\s*!\s*\("


@dataclass
class Arm:
    pattern: str
    body: str
    line: int


@dataclass
class Construct:
    file: str
    line: int
    kind: str
    depth: int = 0
    scrutinee: str = ""
    arms: list[Arm] = field(default_factory=list)
    is_let: bool = False
    counted: bool = False
    tag_dispatch: bool = False
    mutating: bool = False
    state_cells: list[str] = field(default_factory=list)
    contract_start: int = 0
    offset: int = 0
    violations: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Scan:
    path: str
    text: str
    constructs: list[Construct]
    match_count: int
    if_count: int
    parse_errors: list[tuple[int, str]]


def mask(text: str) -> str:
    """Return a same-length copy with comments, strings and backtick URIs blanked."""
    out = list(text)
    index = 0
    size = len(text)
    while index < size:
        char = text[index]
        pair = text[index:index + 2]
        if pair == "//":
            while index < size and text[index] != "\n":
                out[index] = " "
                index += 1
            continue
        if pair == "/*":
            out[index] = out[index + 1] = " "
            index += 2
            while index < size and text[index:index + 2] != "*/":
                if text[index] != "\n":
                    out[index] = " "
                index += 1
            if index < size:
                out[index] = out[index + 1] = " "
                index += 2
            continue
        if char in {'"', "`"}:
            quote = char
            out[index] = " "
            index += 1
            while index < size:
                if text[index] == "\\" and quote == '"' and index + 1 < size:
                    out[index] = out[index + 1] = " "
                    index += 2
                    continue
                if text[index] == quote:
                    out[index] = " "
                    index += 1
                    break
                if text[index] != "\n":
                    out[index] = " "
                index += 1
            continue
        index += 1
    return "".join(out)


def matching(text: str, start: int, open_char: str = "{", close_char: str = "}") -> int:
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def skip_space(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def find_header_body(text: str, start: int, kind: str) -> int:
    """Find the body `{` for a construct whose keyword starts at `start`."""
    index = start
    paren = 0
    bracket = 0
    while index < len(text):
        char = text[index]
        if char == "(":
            paren += 1
        elif char == ")":
            paren = max(0, paren - 1)
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket = max(0, bracket - 1)
        elif char == "{" and paren == 0 and bracket == 0:
            if kind != "match":
                return index
            end = matching(text, index)
            if end < 0:
                return -1
            inner = text[index + 1:end]
            if has_top_level_arrow(inner):
                return index
            index = end
        index += 1
    return -1


def has_top_level_arrow(text: str) -> bool:
    brace = paren = bracket = 0
    index = 0
    while index < len(text) - 1:
        char = text[index]
        if char == "{":
            brace += 1
        elif char == "}":
            brace = max(0, brace - 1)
        elif char == "(":
            paren += 1
        elif char == ")":
            paren = max(0, paren - 1)
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket = max(0, bracket - 1)
        elif char == "=" and text[index + 1] == ">" and brace == paren == bracket == 0:
            return True
        index += 1
    return False


def split_arms(inner: str, raw: str, base_line: int) -> list[Arm]:
    arms: list[Arm] = []
    index = 0
    size = len(inner)
    while index < size:
        start = index
        brace = paren = bracket = 0
        arrow = -1
        while index < size:
            char = inner[index]
            if char == "{":
                brace += 1
            elif char == "}":
                brace = max(0, brace - 1)
            elif char == "(":
                paren += 1
            elif char == ")":
                paren = max(0, paren - 1)
            elif char == "[":
                bracket += 1
            elif char == "]":
                bracket = max(0, bracket - 1)
            elif char == "=" and index + 1 < size and inner[index + 1] == ">" \
                    and brace == paren == bracket == 0:
                arrow = index
                index += 2
                break
            index += 1
        if arrow < 0:
            break
        pattern = raw[start:arrow].strip().strip("|,").strip()
        index = skip_space(inner, index)
        if index < size and inner[index] == "{":
            end = matching(inner, index)
            if end < 0:
                break
            body = raw[index:end + 1]
            index = end + 1
        else:
            newline = inner.find("\n", index)
            if newline < 0:
                body = raw[index:]
                index = size
            else:
                body = raw[index:newline]
                index = newline + 1
        if pattern:
            arms.append(Arm(pattern=pattern, body=body.strip(),
                            line=base_line + inner.count("\n", 0, start)))
        else:
            continue
    return arms


def total_tuple_bind(pattern: str) -> bool:
    text = pattern.strip()
    if not (text.startswith("(") and text.endswith(")")):
        return False
    inner = text[1:-1].strip()
    if not inner:
        return True
    parts = [part.strip() for part in inner.split(",") if part.strip()]
    return bool(parts) and all(
        (part == "_" or IDENT_RE.match(part)) and part not in KEYWORDS
        for part in parts
    )


def is_lone_binder(pattern: str) -> bool:
    return pattern != "_" and bool(IDENT_RE.match(pattern)) and pattern not in KEYWORDS


def boolean_pair(patterns: list[str]) -> bool:
    if len(patterns) != 2:
        return False
    firsts = []
    for pattern in patterns:
        text = pattern.strip()
        if text.startswith("("):
            inner = text[1:-1].strip() if text.endswith(")") else ""
            first = inner.split(",", 1)[0].strip()
        else:
            first = text
        firsts.append(first)
    return set(firsts) == {"true", "false"}


def catch_all_arm(arms: list[Arm]) -> int | None:
    patterns = [arm.pattern for arm in arms]
    if not patterns:
        return None
    for index, pattern in enumerate(patterns):
        if pattern == "_":
            return index
    last = patterns[-1]
    if is_lone_binder(last):
        return len(patterns) - 1
    if total_tuple_bind(last):
        return len(patterns) - 1
    if boolean_pair(patterns):
        return len(patterns) - 1
    return None


def normalize_body(body: str) -> str:
    return re.sub(r"\s+", " ", body).strip()


def condition_text(text: str, start: int) -> tuple[str, int]:
    open_at = text.find("(", start)
    if open_at < 0:
        return "", -1
    close_at = matching(text, open_at, "(", ")")
    if close_at < 0:
        return "", -1
    return text[open_at + 1:close_at].strip(), close_at


def is_tag_dispatch(condition: str) -> bool:
    if any(token in condition for token in ("&&", "||", "<", ">", "!=", "Nil",
                                            "true", "false")):
        return False
    return bool(re.search(r'==\s*(?:"[^"]*"|-?\d+)', condition)
                or re.search(r'(?:"[^"]*"|-?\d+)\s*==', condition))


def state_cells() -> set[str]:
    cells: set[str] = set()
    try:
        doc = json.loads(COMPONENTS.read_text())
    except (OSError, ValueError):
        return cells
    for row in doc.get("components", {}).values():
        cells.update(str(cell) for cell in row.get("state_cells", []))
    return cells


def cell_regex(cells: set[str]) -> re.Pattern[str]:
    known = "|".join(sorted((re.escape(cell) for cell in cells), key=len, reverse=True))
    fallback = r"(?:[A-Za-z_][A-Za-z0-9_']*)?[Ss]tate"
    if known:
        return re.compile(rf"(?:{known}|{fallback})\s*!\s*\(")
    return re.compile(rf"\b{fallback}\s*!\s*\(")


def consumed_cells(text: str, start: int, end: int, cells: set[str]) -> list[str]:
    """Cells consumed in the window whose latest consume has no repost before `end`."""
    consumed: dict[str, int] = {}
    for match in re.finditer(r"\bfor\s*\(", text[start:end]):
        open_at = start + match.end() - 1
        close_at = matching(text, open_at, "(", ")")
        if close_at < 0:
            continue
        head = text[open_at + 1:close_at]
        for part in re.split(r"[;,]", head):
            if "<-" not in part or "<<-" in part:
                continue
            source = part.split("<-", 1)[1].strip()
            name = source.lstrip("@*").split(".", 1)[0].strip()
            if name in cells or re.search(r"[Ss]tate$", name):
                consumed[name] = max(consumed.get(name, -1), start + match.start())
    held: list[str] = []
    for name, at in consumed.items():
        repost = re.compile(re.escape(name) + r"\s*!\s*\(")
        later = [m.start() for m in repost.finditer(text[at:end])]
        if not later:
            held.append(name)
    return sorted(held)


def scan_text(text: str, rel: str, cells: set[str]) -> Scan:
    masked = mask(text)
    errors: list[tuple[int, str]] = []
    constructs: list[Construct] = []
    brace_labels: dict[int, tuple[str, Construct | None]] = {}
    contract_body = -1
    contract_start = 0

    for token in CONTRACT_RE.finditer(masked):
        body = find_header_body(masked, token.start(), "contract")
        if body < 0:
            errors.append((line_of(masked, token.start()), "contract body not found"))
            continue
        brace_labels[body] = ("contract", None)

    for token in MATCH_RE.finditer(masked):
        body = find_header_body(masked, token.start(), "match")
        if body < 0:
            errors.append((line_of(masked, token.start()), "match body not found"))
            continue
        end = matching(masked, body)
        if end < 0:
            errors.append((line_of(masked, token.start()), "match body unclosed"))
            continue
        arms = split_arms(masked[body + 1:end], text[body + 1:end],
                          line_of(masked, body))
        scrutinee = masked[token.end():body].strip()
        let = len(arms) == 1 and (
            is_lone_binder(arms[0].pattern) or total_tuple_bind(arms[0].pattern)
        )
        construct = Construct(
            file=rel,
            line=line_of(masked, token.start()),
            kind="match",
            scrutinee=scrutinee,
            arms=arms,
            is_let=let,
            counted=not let,
            offset=token.start(),
        )
        if not arms:
            construct.violations.append(("M-008", "match has no arms"))
        brace_labels[body] = ("let" if let else "match", construct)
        constructs.append(construct)

    for token in IF_RE.finditer(masked):
        condition, close_at = condition_text(masked, token.start())
        if close_at < 0:
            errors.append((line_of(masked, token.start()), "if condition unclosed"))
            continue
        body = masked.find("{", close_at)
        if body < 0:
            errors.append((line_of(masked, token.start()), "if body not found"))
            continue
        tag = is_tag_dispatch(condition)
        construct = Construct(
            file=rel,
            line=line_of(masked, token.start()),
            kind="if",
            scrutinee=condition,
            tag_dispatch=tag,
            counted=tag,
            offset=token.start(),
        )
        brace_labels[body] = ("if" if tag else "guard", construct)
        constructs.append(construct)

    match_tokens = len(MATCH_RE.findall(masked))
    parsed_matches = sum(1 for item in constructs if item.kind == "match")
    if match_tokens != parsed_matches:
        errors.append((1, f"{match_tokens} match tokens, {parsed_matches} parsed"))

    stack: list[tuple[str, Construct | None, int]] = []
    contract_frames: list[int] = []
    contract_starts: list[int] = []
    for index, char in enumerate(masked):
        if char == "{":
            label, construct = brace_labels.get(index, ("other", None))
            if label == "contract":
                stack.append((label, construct, index))
                contract_frames.append(len(stack) - 1)
                contract_starts.append(index)
                continue
            start = contract_frames[-1] + 1 if contract_frames else 0
            enclosing = sum(1 for kind, _, _ in stack[start:]
                            if kind in ("match", "if"))
            if construct is not None:
                construct.depth = enclosing + (1 if construct.counted else 0)
                construct.contract_start = contract_starts[-1] if contract_starts else 0
                if construct.counted and construct.depth > 3:
                    construct.violations.append(
                        ("M-001", f"dispatch depth {construct.depth} > 3"))
                construct.violations.extend(_ladder_violations(masked, construct))
            stack.append((label, construct, index))
        elif char == "}":
            if stack:
                label, _, _ = stack.pop()
                if label == "contract" and contract_frames \
                        and contract_frames[-1] == len(stack):
                    contract_frames.pop()
                    contract_starts.pop()

    state_re = cell_regex(cells)
    for construct in constructs:
        if construct.kind != "match":
            continue
        construct.state_cells = consumed_cells(
            masked, construct.contract_start, construct.offset, cells)
        # A match is mutating only while it still holds a consumed state cell. A state
        # send nested later in an arm does not make this match the repost owner.
        construct.mutating = bool(construct.state_cells)

        if construct.is_let:
            continue
        total = catch_all_arm(construct.arms)
        if construct.mutating and total is None:
            construct.violations.append(
                ("M-003", "mutating match has no total arm"))
        if construct.mutating and total is not None:
            body = construct.arms[total].body
            has_repost = bool(state_re.search(body))
            has_reply = bool(REPLY_RE.search(body))
            if not ABORT_RE.search(body) and not (has_repost and has_reply):
                construct.violations.append(
                    ("M-004", "total arm must repost the state cell and reply"))
        patterns = [arm.pattern for arm in construct.arms]
        if len(patterns) > 1:
            seen: dict[str, int] = {}
            for index, pattern in enumerate(patterns):
                key = re.sub(r"\s+", " ", pattern).strip()
                if key in seen:
                    construct.violations.append(
                        ("M-005", f"duplicate pattern {pattern!r}"))
                seen[key] = index
            bodies: dict[str, str] = {}
            for arm in construct.arms:
                key = normalize_body(arm.body)
                if key in bodies and normalize_body(arm.pattern) != bodies[key]:
                    construct.violations.append(
                        ("M-005", "identical bodies across distinct arms"))
                    break
                bodies[key] = normalize_body(arm.pattern)
            total_index = catch_all_arm(construct.arms)
            if total_index is not None and total_index != len(construct.arms) - 1:
                construct.violations.append(
                    ("M-005", "catch-all arm is not last"))
        if len(construct.arms) == 1:
            arm = construct.arms[0]
            if arm.pattern == "_" or is_lone_binder(arm.pattern):
                tail = arm.body.strip()
                if tail.startswith("{") and tail.endswith("}"):
                    tail = tail[1:-1].strip()
                if tail.startswith("if"):
                    condition, _ = condition_text(tail, 0)
                    scrutinee = re.sub(r"\s+", " ", construct.scrutinee).strip()
                    if scrutinee and scrutinee in re.sub(r"\s+", " ", condition):
                        construct.violations.append(
                            ("M-006", "dead single-arm match followed by a presence test"))
    return Scan(path=rel, text=masked, constructs=constructs, match_count=match_tokens,
                if_count=len(IF_RE.findall(masked)), parse_errors=errors)


def _offset_of_line(text: str, line: int) -> int:
    if line <= 1:
        return 0
    index = 0
    for _ in range(line - 1):
        found = text.find("\n", index)
        if found < 0:
            return len(text)
        index = found + 1
    return index


def _ladder_violations(masked: str, construct: Construct) -> list[tuple[str, str]]:
    if construct.kind != "if":
        return []
    before = masked[:construct.offset]
    if not before.rstrip().endswith("else"):
        return []
    current, _ = condition_text(masked, construct.offset)
    if "||" in current:
        return []
    head = current.split("==", 1)[0].strip()
    if not head:
        return []
    previous = list(re.finditer(r"\bif\s*\(", before))
    if not previous:
        return []
    prior, _ = condition_text(before, previous[-1].start())
    if "||" in prior:
        return []
    prior_head = prior.split("==", 1)[0].strip()
    if prior_head == head:
        return [("M-002", "same-enum else-if ladder; use a match")]
    return []


def scan_file(path: Path, cells: set[str]) -> Scan:
    return scan_text(path.read_text(), str(path.relative_to(ROOT)), cells)


def scan_all() -> tuple[list[Scan], set[str]]:
    cells = state_cells()
    return [scan_file(path, cells) for path in sorted(CONTRACT_ROOT.rglob("*.rho"))], cells


def summary(scans: list[Scan]) -> dict:
    matches = [item for scan in scans for item in scan.constructs if item.kind == "match"]
    lets = [item for item in matches if item.is_let]
    dispatch = [item for item in matches if not item.is_let]
    violations = [
        (item.file, item.line, code, message)
        for scan in scans for item in scan.constructs
        for code, message in item.violations
    ] + [(scan.path, line, "M-007", message) for scan in scans
         for line, message in scan.parse_errors]
    advisories = [
        (scan.path, item.line, "A-001", "map pattern without ..._")
        for scan in scans for item in scan.constructs if item.kind == "match"
        for arm in item.arms if "{" in arm.pattern and "..." not in arm.pattern
    ]
    return {
        "files": len(scans),
        "match_tokens": sum(scan.match_count for scan in scans),
        "match_sites": len(matches),
        "lets": len(lets),
        "dispatch": len(dispatch),
        "if_count": sum(scan.if_count for scan in scans),
        "mutating": sum(1 for item in matches if item.mutating),
        "max_depth": max((item.depth for item in matches), default=0),
        "depth_histogram": {
            str(depth): sum(1 for item in matches if item.depth == depth)
            for depth in sorted({item.depth for item in matches})
        },
        "violations": violations,
        "advisories": advisories,
    }
