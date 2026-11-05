import type { Capability, ClaimState, PolicyState, RiskState, SlipState, State, SyndicateState } from "./types";

export function capability(allowed: boolean, reason: string): Capability {
  return { allowed, reason };
}

export function isOwner(entity: State, address: string | null, field = "ownerId"): Capability {
  if (!address) return capability(false, "connect a wallet");
  return entity[field] === address
    ? capability(true, "")
    : capability(false, `requires the ${field}`);
}

export function syndicateRole(
  syndicate: SyndicateState,
  address: string | null,
): Capability {
  if (!address) return capability(false, "connect a wallet");
  if (syndicate.ownerId === address) return capability(true, "owner");
  if (syndicate.managerId === address) return capability(true, "manager");
  return capability(false, "requires the syndicate owner or manager");
}

export function riskRole(risk: RiskState, address: string | null): Capability {
  if (!address) return capability(false, "connect a wallet");
  return risk.insured === address || risk.broker === address
    ? capability(true, "insured or broker")
    : capability(false, "requires the insured or broker");
}

export function slipRole(slip: SlipState, address: string | null): Capability {
  if (!address) return capability(false, "connect a wallet");
  if (slip.insured === address) return capability(true, "insured");
  if (slip.brokerOwner === address || slip.broker === address) {
    return capability(true, "broker");
  }
  return capability(false, "requires the insured or broker");
}

export function policyRole(policy: PolicyState, address: string | null): Capability {
  if (!address) return capability(false, "connect a wallet");
  if (policy.insured === address) return capability(true, "insured");
  if (policy.brokerOwner === address || policy.broker === address) {
    return capability(true, "broker");
  }
  return capability(false, "requires the insured or broker");
}

export function claimManager(claim: ClaimState, address: string | null): Capability {
  if (!address) return capability(false, "connect a wallet");
  if (claim.leadManager === address) return capability(true, "lead manager");
  if (claim.secondManager === address) return capability(true, "second manager");
  return capability(false, "requires a line manager");
}
