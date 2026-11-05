#!/usr/bin/env python3
"""Per-scenario conservation gate for the Lloyd's placement.

The gate tracks a closed set of REV holders: the actors' r-cash accounts, the central
fund purse and the syndicate purse.  The syndicate purse is not directly readable, but
the contracts keep its balance exactly equal to ``capital + premiums``: contributions
raise both, line credits raise ``premiums``, and a line payout lowers ``capital``.  A
slip whose premium is funded but not yet bound holds the premium in its own purse, so
the slip's ``funded`` amount is counted as escrow until the slip is bound or expired.

Every terminal path must leave the total constant.  Premium is not conserved as one
balance: it splits into the broker commission, the central-fund levy and the line
credits according to the cover terms.  Settlement then moves value from the syndicate
purse (and, if used, the fund) back to the insured.
"""

from __future__ import annotations

import argparse

import actors
from placement_fixture import Placement, started

from preflight import require_devnet


def _account_names(placement: Placement) -> list[str]:
    return list(dict.fromkeys(
        (placement.insured, placement.broker_owner,
         placement.syndicate_owner, placement.platform)))


def snapshot(placement: Placement, claim_id: str | None = None) -> dict:
    """Read every balance the placement can move, plus the derived syndicate purse."""
    syndicate = placement.syndicate_info()
    accounts = {
        name: actors.balance(name) for name in _account_names(placement)}
    slip = placement.slip_info() if placement.slip_uri else {}
    slip_funded = 0
    if slip.get("status") in {"open", "subscribed"}:
        slip_funded = int(slip.get("funded", 0))
    lines = {line["lineId"]: line for line in placement.lines_info()}
    premium = expected_split(placement)
    premium["line_credits_actual"] = sum(
        int(line.get("credited", 0)) for line in lines.values())
    return {
        "accounts": accounts,
        "premium": premium,
        "insured": accounts.get(placement.insured, 0),
        "broker": accounts.get(placement.broker_owner, 0),
        "platform": accounts.get(placement.platform, 0),
        "fund": placement.fund_balance(),
        "slip_funded": slip_funded,
        "syndicate": {
            "capital": int(syndicate.get("capital", 0)),
            "written": int(syndicate.get("written", 0)),
            "premiums": int(syndicate.get("premiums", 0)),
            "claims_paid": int(syndicate.get("claimsPaid", 0)),
            "purse": int(syndicate.get("capital", 0))
                     + int(syndicate.get("premiums", 0)),
        },
        "lines": {
            line_id: {
                "credited": int(line.get("credited", 0)),
                "paid": int(line.get("paid", 0)),
                "exposure": int(line.get("exposure", 0)),
            }
            for line_id, line in lines.items()
        },
        "cover": placement.fund_cover(claim_id) if placement.policy_uri else 0,
    }


def total(values: dict) -> int:
    """Total tracked REV: accounts plus fund plus syndicate purse plus slip escrow."""
    return (sum(values["accounts"].values())
            + int(values["fund"])
            + int(values["syndicate"]["purse"])
            + int(values["slip_funded"]))


def expected_split(placement: Placement) -> dict:
    """Commission, levy and line credits the cover terms imply."""
    premium = int(placement.terms["premiumTotal"])
    commission = premium * int(placement.terms["brokerCommissionBps"]) // 10_000
    levy = premium * int(placement.terms["centralFundBps"]) // 10_000
    return {"premium": premium, "commission": commission, "levy": levy,
            "line_credits": premium - commission - levy}


def check_conserved(before: dict, after: dict, label: str = "conservation") -> None:
    if total(before) != total(after):
        raise AssertionError(
            f"{label}: total moved {total(before)} -> {total(after)} "
            f"({before!r} -> {after!r})")
    print(f"  ok {label} {total(before)}")


def expect_delta(label: str, actual: int, expected: int) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected}, got {actual}")
    print(f"  ok {label} {expected:+d}")


def check_premium(placement: Placement, before: dict, after: dict) -> dict:
    """Assert the premium split and that the total stayed constant."""
    check_conserved(before, after, "premium conservation")
    expected = expected_split(placement)
    line_credits = sum(line["credited"] for line in after["lines"].values())
    fund_delta = int(after["fund"]) - int(before["fund"])
    commission = expected["premium"] - fund_delta - line_credits
    if line_credits != expected["line_credits"]:
        raise AssertionError(
            f"line credits: expected {expected['line_credits']}, got {line_credits}")
    if fund_delta != expected["levy"]:
        raise AssertionError(
            f"fund levy: expected {expected['levy']}, got {fund_delta}")
    if commission != expected["commission"]:
        raise AssertionError(
            f"commission: expected {expected['commission']}, got {commission}")
    print(f"  ok premium split {expected['premium']} = "
          f"{commission} commission + {fund_delta} levy + {line_credits} credits")
    return expected


def check_payout(placement: Placement, before: dict, after: dict,
                 claim_id: str | None = None) -> dict:
    """Assert line payouts plus fund cover equal the claim's paid amount."""
    claim = placement.claim_info()
    payable = int(claim.get("paid", claim.get("agreedAmount", 0)))
    line_paid = sum(line["paid"] for line in after["lines"].values())
    cover = after["cover"]
    if line_paid + cover != payable:
        raise AssertionError(
            f"payout: lines {line_paid} + fund {cover} != paid {payable} "
            f"({claim!r})")
    fund_delta = int(after["fund"]) - int(before["fund"])
    claims_delta = (int(after["syndicate"]["claims_paid"])
                    - int(before["syndicate"]["claims_paid"]))
    if claims_delta != line_paid:
        raise AssertionError(
            f"syndicate claimsPaid: expected {line_paid}, got {claims_delta}")
    if fund_delta != -cover:
        raise AssertionError(f"fund cover: expected {-cover}, got {fund_delta}")
    print(f"  ok payout {payable} = {line_paid} lines + {cover} fund cover")
    return {"payable": payable, "line_paid": line_paid, "cover": cover}


def check_lines(placement: Placement) -> None:
    for line in placement.lines_info():
        if line["paid"] > line["exposure"]:
            raise AssertionError(f"line paid above exposure: {line!r}")
    print(f"  ok {len(placement.lines_info())} line(s) within exposure")


# ---- scenarios -----------------------------------------------------------------------


def scenario_premium(name: str = "premium") -> dict:
    print(f"  scenario premium_distribution ({name})")
    placement = started(name)
    before = snapshot(placement)
    placement.bind_all()
    after = snapshot(placement)
    expected = check_premium(placement, before, after)
    check_lines(placement)
    if after["slip_funded"] != 0:
        raise AssertionError(f"bound slip still holds escrow: {after['slip_funded']}")
    return {"before": before, "after": after, "expected": expected}


def scenario_settlement(name: str = "settlement", amount: int | None = None) -> dict:
    print(f"  scenario claim_settlement ({name})")
    placement = started(name)
    placement.bind_all()
    before = snapshot(placement)
    placement.claim(amount=amount)
    after = snapshot(placement)
    check_conserved(before, after, "settlement conservation")
    result = check_payout(placement, before, after, placement.claim_id)
    check_lines(placement)
    return {"before": before, "after": after, "payout": result}


def negative_control(name: str = "negative-control") -> int:
    """Omit the slip escrow; the total must visibly drop when the premium is funded."""
    print(f"  negative control ({name})")
    placement = started(name)
    before = snapshot(placement)
    placement.subscribe()
    placement.accept()
    placement.fund_premium()
    funded = snapshot(placement)
    if total(funded) != total(before):
        raise AssertionError(
            f"funding moved the tracked total: {total(before)} -> {total(funded)}")
    without_escrow = total(funded) - funded["slip_funded"]
    if without_escrow == total(before):
        raise AssertionError("negative control failed to detect the slip escrow")
    print(f"  ok negative control: untracked slip escrow detected "
          f"({total(before)} -> {without_escrow})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative-control", action="store_true",
                    help="prove the total assertion detects untracked slip escrow")
    ap.add_argument("--scenario", choices=("premium", "settlement", "all"),
                    default="all")
    args = ap.parse_args(argv)
    if not require_devnet("conservation"):
        return 2
    print("conservation")
    if args.negative_control:
        return negative_control()
    if args.scenario in ("premium", "all"):
        scenario_premium()
    if args.scenario in ("settlement", "all"):
        scenario_settlement()
    print("conservation: all scenarios conserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
