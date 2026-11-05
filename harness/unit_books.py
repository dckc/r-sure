#!/usr/bin/env python3
"""PolicyBook and ClaimBook: registration, indexes and unknown-id refusals."""

import sys

import actors
import assertions as A
import placement_fixture as F
import preflight


def main() -> int:
    if not preflight.require_devnet("books"):
        print("not_run: devnet unavailable")
        return 2
    try:
        p = F.bound("books", syndicate_owner="deployer")
        policy_book = p.component("component:policy-book")
        claim_book = p.component("component:claim-book")
        policy_id = p.policy_info().get("id")

        A.cover('PolicyBook@"policies"', "success")
        policies = actors.invoke(policy_book, "policies")
        A.expect("policy registered", policy_id in policies[1], True)
        A.cover('PolicyBook@"policy"', "success")
        A.expect("policy lookup", actors.invoke(policy_book, "policy", f'"{policy_id}"'),
                 (True, p.policy_uri))
        A.cover('PolicyBook@"byInsured"', "success")
        A.expect("policy by insured", policy_id in actors.invoke(
            policy_book, "byInsured", f'"{p.owner_id}"')[1], True)
        A.cover('PolicyBook@"byBroker"', "success")
        A.expect("policy by broker", policy_id in actors.invoke(
            policy_book, "byBroker", f'"{p.broker_id}"')[1], True)
        A.cover('PolicyBook@"bySlip"', "success")
        A.expect("policy by slip", policy_id in actors.invoke(
            policy_book, "bySlip", f'"{p.slip_id}"')[1], True)
        A.cover('PolicyBook@"policy"', "refusal")
        A.expect_refusal("unknown policy", actors.invoke(
            policy_book, "policy", '"pol:missing"'), "unknown policy")

        claim_id, claim_uri = p.open_claim(amount=100)
        A.cover('ClaimBook@"claims"', "success")
        claims = actors.invoke(claim_book, "claims")
        A.expect("claim registered", claim_id in claims[1], True)
        A.cover('ClaimBook@"claim"', "success")
        A.expect("claim lookup", actors.invoke(claim_book, "claim", f'"{claim_id}"'),
                 (True, claim_uri))
        A.cover('ClaimBook@"byPolicy"', "success")
        A.expect("claim by policy", claim_id in actors.invoke(
            claim_book, "byPolicy", f'"{policy_id}"')[1], True)
        A.cover('ClaimBook@"byInsured"', "success")
        A.expect("claim by insured", claim_id in actors.invoke(
            claim_book, "byInsured", f'"{p.owner_id}"')[1], True)
        A.cover('ClaimBook@"claim"', "refusal")
        A.expect_refusal("unknown claim", actors.invoke(
            claim_book, "claim", '"clm:missing"'), "unknown claim")
    except Exception as error:
        print(f"books suite failed: {error}", file=sys.stderr)
        A.finish("books")
        return 1
    return A.finish("books")


if __name__ == "__main__":
    raise SystemExit(main())
