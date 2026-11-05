//! Pure r-sure types, coverage terms and integer arithmetic.

#![forbid(unsafe_code)]

pub mod error;
pub mod evidence;
pub mod ids;
pub mod math;
pub mod primitives;
pub mod render;
pub mod status;
pub mod terms;

pub use error::CoreError;
pub use evidence::{EvidenceKind, EvidenceRef};
pub use ids::{BrokerId, ClaimId, LineId, PolicyId, RiskId, SlipId, SyndicateId};
pub use math::{line_shares, payable, premium_split, split_bps};
pub use primitives::{Amount, BasisPoints, Height, Nonce, OwnerId};
pub use status::{ClaimStatus, CoverStatus, LineStatus, PolicyStatus, SlipStatus, SyndicateStatus};
pub use terms::{CoverTerms, RiskClass};

/// The hard client budget for one deploy term; the node cap is 64 KiB.
pub const PROJECT_TERM_BUDGET: usize = 56 * 1024;

/// Basis-point denominator.
pub const BPS_DENOMINATOR: u64 = 10_000;
