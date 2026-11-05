use serde::{Deserialize, Serialize};

use crate::error::CoreError;

macro_rules! id_newtype {
    ($name:ident, $prefix:literal) => {
        #[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
        #[serde(transparent)]
        pub struct $name(String);

        impl $name {
            pub fn new(value: impl Into<String>) -> Result<Self, CoreError> {
                let value = value.into();
                if value.is_empty() {
                    return Err(CoreError::OwnerId);
                }
                Ok(Self(value))
            }

            pub fn from_parts(parts: &[&str]) -> Self {
                Self(format!("{}{}", $prefix, parts.join(":")))
            }

            pub fn as_str(&self) -> &str {
                &self.0
            }
        }

        impl std::fmt::Display for $name {
            fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                self.0.fmt(f)
            }
        }
    };
}

id_newtype!(SyndicateId, "syn:");
id_newtype!(BrokerId, "brk:");
id_newtype!(RiskId, "rsk:");
id_newtype!(SlipId, "slp:");
id_newtype!(PolicyId, "pol:");
id_newtype!(LineId, "lin:");
id_newtype!(ClaimId, "clm:");
