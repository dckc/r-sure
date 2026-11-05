use serde::{Deserialize, Serialize};

macro_rules! status {
    ($name:ident { $($variant:ident => $text:literal),+ $(,)? }) => {
        #[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
        pub enum $name {
            $($variant,)+
            Unknown(String),
        }

        impl $name {
            pub fn as_str(&self) -> &str {
                match self {
                    $(Self::$variant => $text,)+
                    Self::Unknown(value) => value.as_str(),
                }
            }

            pub fn parse(value: &str) -> Self {
                match value {
                    $($text => Self::$variant,)+
                    other => Self::Unknown(other.to_owned()),
                }
            }
        }
    };
}

status!(SyndicateStatus {
    Active => "active",
    Suspended => "suspended",
    Closed => "closed",
});

status!(SlipStatus {
    Open => "open",
    Subscribed => "subscribed",
    Funded => "funded",
    Bound => "bound",
    Expired => "expired",
    Cancelled => "cancelled",
});

status!(PolicyStatus {
    Active => "active",
    Expired => "expired",
    Cancelled => "cancelled",
    Closed => "closed",
});

status!(ClaimStatus {
    Notified => "notified",
    Classified => "classified",
    Assessed => "assessed",
    Agreed => "agreed",
    Disputed => "disputed",
    Upheld => "upheld",
    PartiallyUpheld => "partially_upheld",
    Denied => "denied",
    Settled => "settled",
    Closed => "closed",
});

status!(LineStatus {
    Bound => "bound",
    Released => "released",
    Exhausted => "exhausted",
});

status!(CoverStatus {
    Open => "open",
    Consumed => "consumed",
    Revoked => "revoked",
    Expired => "expired",
});
