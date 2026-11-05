//! Component keys registered in SureRoot and their install-manifest slots.

use serde::{Deserialize, Serialize};

/// Every component key the installer registers.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ComponentKey {
    Clock,
    Verifier,
    Codec,
    AdminGuard,
    Admin,
    Terms,
    SureMath,
    Rgen,
    Payments,
    SyndicateBook,
    BrokerBook,
    RiskBook,
    SlipFactory,
    LineFactory,
    DistributionFactory,
    Fund,
    PolicyFactory,
    ClaimFactory,
    PolicyBook,
    ClaimBook,
}

impl ComponentKey {
    pub const ALL: [Self; 20] = [
        Self::Clock,
        Self::Verifier,
        Self::Codec,
        Self::AdminGuard,
        Self::Admin,
        Self::Terms,
        Self::SureMath,
        Self::Rgen,
        Self::Payments,
        Self::SyndicateBook,
        Self::BrokerBook,
        Self::RiskBook,
        Self::SlipFactory,
        Self::LineFactory,
        Self::DistributionFactory,
        Self::Fund,
        Self::PolicyFactory,
        Self::ClaimFactory,
        Self::PolicyBook,
        Self::ClaimBook,
    ];

    /// The registry key used by `SureRoot.resolve`.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Clock => "component:clock",
            Self::Verifier => "component:verifier",
            Self::Codec => "component:codec",
            Self::AdminGuard => "component:admin-guard",
            Self::Admin => "component:admin",
            Self::Terms => "component:terms",
            Self::SureMath => "component:suremath",
            Self::Rgen => "component:rgen",
            Self::Payments => "component:payments",
            Self::SyndicateBook => "component:syndicate-book",
            Self::BrokerBook => "component:broker-book",
            Self::RiskBook => "component:risk-book",
            Self::SlipFactory => "component:slip-factory",
            Self::LineFactory => "component:line-factory",
            Self::DistributionFactory => "component:distribution-factory",
            Self::Fund => "component:fund",
            Self::PolicyFactory => "component:policy-factory",
            Self::ClaimFactory => "component:claim-factory",
            Self::PolicyBook => "component:policy-book",
            Self::ClaimBook => "component:claim-book",
        }
    }

    /// The deploy term that registers this component.
    pub const fn manifest_file(self) -> &'static str {
        match self {
            Self::Clock | Self::Verifier | Self::Codec => "01_kernel.rho",
            Self::AdminGuard | Self::Admin => "02_admin.rho",
            Self::Terms => "03_terms.rho",
            Self::SureMath => "04_math.rho",
            Self::Rgen => "05_rgen.rho",
            Self::Payments => "40_payments.rho",
            Self::DistributionFactory => "15_distribution.rho",
            Self::Fund => "16_fund.rho",
            Self::SyndicateBook => "10_syndicate.rho",
            Self::BrokerBook => "11_broker.rho",
            Self::RiskBook => "12_risk.rho",
            Self::SlipFactory => "13_slip.rho",
            Self::LineFactory => "14_line.rho",
            Self::PolicyFactory => "17_policy.rho",
            Self::ClaimFactory => "18_claim.rho",
            Self::PolicyBook | Self::ClaimBook => "19_books.rho",
        }
    }

    /// The component's position in its deploy term's return list.
    pub const fn manifest_index(self) -> usize {
        match self {
            Self::Clock => 0,
            Self::Verifier => 1,
            Self::Codec => 2,
            Self::AdminGuard => 0,
            Self::Admin => 1,
            Self::Terms
            | Self::SureMath
            | Self::Rgen
            | Self::Payments
            | Self::DistributionFactory
            | Self::Fund
            | Self::SyndicateBook
            | Self::BrokerBook
            | Self::RiskBook
            | Self::SlipFactory
            | Self::LineFactory
            | Self::PolicyFactory
            | Self::ClaimFactory => 0,
            Self::PolicyBook => 0,
            Self::ClaimBook => 1,
        }
    }

    pub fn parse(value: &str) -> Option<Self> {
        let full = if value.starts_with("component:") {
            value.to_string()
        } else {
            format!("component:{value}")
        };
        Self::ALL.into_iter().find(|key| key.as_str() == full)
    }
}

impl std::fmt::Display for ComponentKey {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(self.as_str())
    }
}
