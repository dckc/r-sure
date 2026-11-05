//! Connected r-sure client over the r-cash signed-deploy client.

#![forbid(unsafe_code)]

pub mod client;
pub mod error;
pub mod funding;
pub mod models;
pub mod wire;

pub use client::{Client, ResolvedComponent};
pub use error::{DecodeError, DecodeKind, RefusalCode, SdkError};
pub use models::{ClaimView, PolicyView, SlipView, SyndicateView};
pub use wire::{DeployReceipt, Read, ReadMeta, ReadSource, Write};

/// A deterministic component key for a client read.
pub fn component_key(name: &str) -> String {
    format!("component:{name}")
}
