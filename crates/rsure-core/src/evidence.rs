use serde::{Deserialize, Serialize};

use crate::error::CoreError;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvidenceKind {
    RgenIdentity,
    RgenCredential,
    RgenClaim,
    RgenValidation,
    RgenKasset,
    RgenProvenance,
    RgenOracleCase,
    ExternalReport,
    ExternalDocument,
    Unknown(String),
}

impl EvidenceKind {
    pub fn as_str(&self) -> &str {
        match self {
            Self::RgenIdentity => "rgen:identity",
            Self::RgenCredential => "rgen:credential",
            Self::RgenClaim => "rgen:claim",
            Self::RgenValidation => "rgen:validation",
            Self::RgenKasset => "rgen:kasset",
            Self::RgenProvenance => "rgen:provenance",
            Self::RgenOracleCase => "rgen:oracle-case",
            Self::ExternalReport => "external:report",
            Self::ExternalDocument => "external:document",
            Self::Unknown(value) => value.as_str(),
        }
    }

    pub fn parse(value: &str) -> Self {
        match value {
            "rgen:identity" => Self::RgenIdentity,
            "rgen:credential" => Self::RgenCredential,
            "rgen:claim" => Self::RgenClaim,
            "rgen:validation" => Self::RgenValidation,
            "rgen:kasset" => Self::RgenKasset,
            "rgen:provenance" => Self::RgenProvenance,
            "rgen:oracle-case" => Self::RgenOracleCase,
            "external:report" => Self::ExternalReport,
            "external:document" => Self::ExternalDocument,
            other => Self::Unknown(other.to_owned()),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceRef {
    pub kind: String,
    pub uri: String,
    pub hash: String,
}

impl EvidenceRef {
    pub fn validate(&self) -> Result<(), CoreError> {
        if self.hash.is_empty() || self.hash.len() > 128 {
            return Err(CoreError::Evidence);
        }
        if self.kind.starts_with("rgen:") && !self.uri.starts_with("rho:id:") {
            return Err(CoreError::Evidence);
        }
        Ok(())
    }
}
