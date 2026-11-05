//! Connected r-sure client.
//!
//! The scaffold defines the configuration boundary and the wire/model modules. The
//! `rcash_sdk::Client` wrapper, signed writes and funding bridge are the next implementation
//! step; the contracts and the static gates do not depend on them.

#![forbid(unsafe_code)]

pub mod models;
pub mod wire;

pub use models::{ClaimView, PolicyView, SlipView, SyndicateView};
pub use wire::{ClientConfig, ReadSource};

#[derive(Debug, Clone)]
pub struct Client {
    config: ClientConfig,
}

impl Client {
    pub fn new(config: ClientConfig) -> Self {
        Self { config }
    }

    pub fn config(&self) -> &ClientConfig {
        &self.config
    }

    /// A deterministic component key for a client read.
    pub fn component_key(name: &str) -> String {
        format!("component:{name}")
    }
}
