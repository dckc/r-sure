use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum CoreError {
    #[error("amount must be non-negative")]
    Amount,
    #[error("basis points must be in 0..=10000")]
    BasisPoints,
    #[error("height is out of range")]
    Height,
    #[error("nonce is out of range")]
    Nonce,
    #[error("owner id is empty")]
    OwnerId,
    #[error("coverage term is invalid: {0}")]
    Terms(&'static str),
    #[error("shares must sum to 10000")]
    Shares,
    #[error("a line share is out of range")]
    LineShare,
    #[error("render refuses floats, negative or wide integers")]
    Render,
    #[error("evidence reference is invalid")]
    Evidence,
    #[error("unknown status: {0}")]
    UnknownStatus(String),
    #[error("manifest is invalid: {0}")]
    Manifest(String),
}
