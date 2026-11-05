//! SDK errors and refusal classification.

use std::fmt;

use rcash_chain::ChainError;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DecodeKind {
    Missing,
    WrongType,
    OutOfRange,
    UnknownTag,
    UnsupportedSchema,
}

impl fmt::Display for DecodeKind {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Missing => "missing",
            Self::WrongType => "wrong type",
            Self::OutOfRange => "out of range",
            Self::UnknownTag => "unknown tag",
            Self::UnsupportedSchema => "unsupported schema",
        })
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DecodeError {
    pub context: String,
    pub field: String,
    pub kind: DecodeKind,
}

impl DecodeError {
    pub fn new(context: impl Into<String>, field: impl Into<String>, kind: DecodeKind) -> Self {
        Self {
            context: context.into(),
            field: field.into(),
            kind,
        }
    }
}

impl fmt::Display for DecodeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{}: field `{}` is {}",
            self.context, self.field, self.kind
        )
    }
}

impl std::error::Error for DecodeError {}

/// The published refusal vocabulary, grouped for the UI.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RefusalCode {
    NotOwner,
    NotInsured,
    NotManager,
    NotLead,
    NotHolder,
    Closed,
    Replay,
    Paused,
    Frozen,
    Stale,
    Duplicate,
    Capacity,
    Amount,
    Terms,
    Share,
    Asset,
    Bps,
    BelowThreshold,
    NotActive,
    NotAccepted,
    NotFunded,
    NotSubscribed,
    NotAssessed,
    NotClassified,
    Exhausted,
    AlreadySettled,
    UnknownComponent,
    PaymentsUnavailable,
    RgenUnavailable,
    ClockUnavailable,
    Other(String),
}

impl RefusalCode {
    pub fn classify(reason: &str) -> Self {
        match reason {
            "not owner" | "not installer" => Self::NotOwner,
            "not insured" => Self::NotInsured,
            "not manager" => Self::NotManager,
            "not lead" => Self::NotLead,
            "not holder" => Self::NotHolder,
            "closed" | "not expired" => Self::Closed,
            "replay" => Self::Replay,
            "paused" => Self::Paused,
            "frozen" => Self::Frozen,
            "stale" => Self::Stale,
            "duplicate" | "duplicate owner" | "duplicate syndicate" => Self::Duplicate,
            "capacity" => Self::Capacity,
            "amount" => Self::Amount,
            "terms" => Self::Terms,
            "share" | "shares" => Self::Share,
            "asset" => Self::Asset,
            "bps" => Self::Bps,
            "below threshold" => Self::BelowThreshold,
            "not active" => Self::NotActive,
            "not accepted" => Self::NotAccepted,
            "not funded" => Self::NotFunded,
            "not fully subscribed" => Self::NotSubscribed,
            "not assessed" => Self::NotAssessed,
            "not classified" => Self::NotClassified,
            "exhausted" => Self::Exhausted,
            "already settled" => Self::AlreadySettled,
            "unknown component" => Self::UnknownComponent,
            "payments unavailable" | "rcash unavailable" => Self::PaymentsUnavailable,
            "rgen unavailable" | "rgen disabled" | "oracle unavailable" => Self::RgenUnavailable,
            "clock unavailable" => Self::ClockUnavailable,
            other => Self::Other(other.to_string()),
        }
    }
}

pub type Result<T> = std::result::Result<T, SdkError>;

#[derive(Debug, thiserror::Error)]
pub enum SdkError {
    #[error(transparent)]
    Chain(#[from] ChainError),
    #[error(transparent)]
    Core(#[from] rsure_core::CoreError),
    #[error("decode error: {0}")]
    Decode(#[from] DecodeError),
    #[error("refused: {reason}")]
    Refused { reason: String, code: RefusalCode },
    #[error("deploy failed: {error}")]
    DeployFailed {
        error: String,
        block_hash: Option<String>,
    },
    #[error("deploy {deploy_id} did not settle: {last}")]
    Unknown { deploy_id: String, last: String },
    #[error("wallet is locked")]
    NoKey,
    #[error("term is {bytes} bytes; the budget is {budget}")]
    TermTooLarge { bytes: usize, budget: usize },
    #[error("manifest is invalid: {0}")]
    Manifest(String),
}

impl SdkError {
    pub fn refused(reason: impl Into<String>) -> Self {
        let reason = reason.into();
        let code = RefusalCode::classify(&reason);
        Self::Refused { reason, code }
    }

    pub fn decode(context: impl Into<String>, field: impl Into<String>, kind: DecodeKind) -> Self {
        Self::Decode(DecodeError::new(context, field, kind))
    }
}
