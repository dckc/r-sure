use serde::{Deserialize, Serialize};

use crate::error::CoreError;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum RiskClass {
    Engineering,
    Property,
    Equipment,
    Liability,
    Marine,
    Cyber,
}

impl RiskClass {
    pub const ALL: [Self; 6] = [
        Self::Engineering,
        Self::Property,
        Self::Equipment,
        Self::Liability,
        Self::Marine,
        Self::Cyber,
    ];

    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Engineering => "engineering",
            Self::Property => "property",
            Self::Equipment => "equipment",
            Self::Liability => "liability",
            Self::Marine => "marine",
            Self::Cyber => "cyber",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoverTerms {
    pub coverage_class: RiskClass,
    pub asset_id: String,
    pub aggregate_limit: u64,
    pub per_claim_limit: u64,
    pub deductible: u64,
    pub premium_total: u64,
    pub period_start_height: u64,
    pub period_end_height: u64,
    pub waiting_blocks: u64,
    pub notice_blocks: u64,
    pub run_off_blocks: u64,
    pub standard_claim_max: u64,
    pub min_syndicates: u8,
    pub max_syndicates: u8,
    pub broker_commission_bps: u16,
    pub central_fund_bps: u16,
    pub evidence_policy: String,
    pub claims_lead_policy: String,
}

impl CoverTerms {
    pub fn validate(&self) -> Result<(), CoreError> {
        if self.asset_id.is_empty() || self.asset_id.len() > 32 {
            return Err(CoreError::Terms("asset"));
        }
        if self.aggregate_limit == 0 || self.per_claim_limit == 0 {
            return Err(CoreError::Terms("limits"));
        }
        if self.per_claim_limit > self.aggregate_limit {
            return Err(CoreError::Terms("limits"));
        }
        if self.deductible >= self.per_claim_limit {
            return Err(CoreError::Terms("deductible"));
        }
        if self.standard_claim_max > self.per_claim_limit {
            return Err(CoreError::Terms("threshold"));
        }
        if self.period_end_height <= self.period_start_height {
            return Err(CoreError::Terms("period"));
        }
        if self.min_syndicates == 0
            || self.min_syndicates > self.max_syndicates
            || self.max_syndicates > 8
        {
            return Err(CoreError::Terms("syndicates"));
        }
        if self.broker_commission_bps as u32 + self.central_fund_bps as u32 > 3_000 {
            return Err(CoreError::Terms("bps"));
        }
        if !matches!(
            self.evidence_policy.as_str(),
            "none" | "optional" | "required"
        ) {
            return Err(CoreError::Terms("evidence"));
        }
        if !matches!(self.claims_lead_policy.as_str(), "lead" | "lead+second") {
            return Err(CoreError::Terms("claims lead"));
        }
        Ok(())
    }
}
