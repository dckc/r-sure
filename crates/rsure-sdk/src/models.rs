use serde::{Deserialize, Serialize};

use rsure_core::{BasisPoints, ClaimStatus, PolicyStatus, SlipStatus, SyndicateStatus};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyndicateView {
    pub id: String,
    pub owner_id: String,
    pub manager_id: String,
    pub capital: u64,
    pub committed: u64,
    pub written: u64,
    pub status: SyndicateStatus,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SlipView {
    pub id: String,
    pub insured: String,
    pub broker: String,
    pub premium_total: u64,
    pub funded: u64,
    pub status: SlipStatus,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PolicyView {
    pub id: String,
    pub insured: String,
    pub aggregate_limit: u64,
    pub aggregate_remaining: u64,
    pub per_claim_limit: u64,
    pub deductible: u64,
    pub status: PolicyStatus,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClaimView {
    pub id: String,
    pub policy_id: String,
    pub claimed_amount: u64,
    pub agreed_amount: u64,
    pub paid: u64,
    pub status: ClaimStatus,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LineView {
    pub line_id: String,
    pub policy: String,
    pub syndicate: String,
    pub share_bps: BasisPoints,
    pub exposure: u64,
    pub paid: u64,
}
