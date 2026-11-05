//! Connected r-sure client over the r-cash signed-deploy client.

use std::collections::BTreeMap;
use std::sync::Mutex;

use rcash_chain::node::pool::{DiscoveryMode, PoolOptions};
use rcash_chain::node::{DeployStatus, NodeClient};
use rcash_chain::rho_expr::RhoValue;
use rcash_chain::KeyPair;
use rcash_sdk::Client as RcashClient;
use rsure_core::{ComponentKey, Manifest};
use serde_json::Value;

use crate::error::{DecodeKind, Result, SdkError};
use crate::wire::{self, Read, Write};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ResolvedComponent {
    pub uri: String,
    pub version: i64,
}

pub struct Client {
    inner: RcashClient,
    manifest: Manifest,
    shard: String,
    phlo_limit: i64,
    phlo_price: i64,
    cache: Mutex<BTreeMap<ComponentKey, ResolvedComponent>>,
}

impl Client {
    pub const DEFAULT_PHLO_LIMIT: i64 = 4_000_000;
    pub const DEFAULT_PHLO_PRICE: i64 = 1;
    pub const DEFAULT_SHARD: &'static str = "/root";

    pub fn reader(node: &str, manifest: Manifest) -> Result<Self> {
        Self::build(node, manifest, None)
    }

    pub fn new(node: &str, manifest: Manifest, key: KeyPair) -> Result<Self> {
        Self::build(node, manifest, Some(key))
    }

    pub fn with_node(node: NodeClient, manifest: Manifest, key: Option<KeyPair>) -> Result<Self> {
        let inner = RcashClient::with_node(node, key)
            .with_shard(Self::DEFAULT_SHARD)
            .with_phlo(Self::DEFAULT_PHLO_LIMIT, Self::DEFAULT_PHLO_PRICE);
        Ok(Self {
            inner,
            manifest,
            shard: Self::DEFAULT_SHARD.to_string(),
            phlo_limit: Self::DEFAULT_PHLO_LIMIT,
            phlo_price: Self::DEFAULT_PHLO_PRICE,
            cache: Mutex::new(BTreeMap::new()),
        })
    }

    fn build(node: &str, manifest: Manifest, key: Option<KeyPair>) -> Result<Self> {
        let node_client = node_client(node, Self::DEFAULT_SHARD)?;
        Self::with_node(node_client, manifest, key)
    }

    pub fn set_network(&mut self, shard: &str, phlo_limit: i64, phlo_price: i64) {
        self.inner
            .set_network(shard.to_string(), phlo_limit, phlo_price);
        self.shard = shard.to_string();
        self.phlo_limit = phlo_limit;
        self.phlo_price = phlo_price;
        self.cache_lock().clear();
    }

    fn cache_lock(&self) -> std::sync::MutexGuard<'_, BTreeMap<ComponentKey, ResolvedComponent>> {
        self.cache
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner)
    }

    pub fn manifest(&self) -> &Manifest {
        &self.manifest
    }

    pub fn key(&self) -> Option<&KeyPair> {
        self.inner.key()
    }

    pub fn has_key(&self) -> bool {
        self.inner.key().is_some()
    }

    pub fn address(&self) -> Result<String> {
        Ok(self.inner.address()?)
    }

    pub fn shard(&self) -> &str {
        &self.shard
    }

    pub fn phlo(&self) -> (i64, i64) {
        (self.phlo_limit, self.phlo_price)
    }

    pub fn node(&self) -> &NodeClient {
        self.inner.node()
    }

    pub async fn height(&self) -> Result<i64> {
        Ok(self.inner.height().await?)
    }

    pub async fn status(&self) -> Result<Value> {
        Ok(self.inner.node().status().await?)
    }

    pub async fn deploy_status(&self, deploy_id: &str) -> Result<DeployStatus> {
        Ok(self.inner.node().deploy_status(deploy_id).await?)
    }

    /// Resolve a component through SureRoot. Results are cached for the client's life.
    pub async fn resolve(&self, key: ComponentKey) -> Result<ResolvedComponent> {
        if let Some(hit) = self.cache_lock().get(&key).cloned() {
            return Ok(hit);
        }
        let term = wire::resolve_term(self.manifest.root_uri(), key.as_str(), 1)?;
        let (value, _meta) = wire::explore_value(&self.inner, &term).await?;
        let values = wire::decode_reply(&value)?;
        let resolved = parse_resolved(&values)?;
        self.cache_lock().insert(key, resolved.clone());
        Ok(resolved)
    }

    pub async fn resolve_all(&self) -> Result<BTreeMap<ComponentKey, ResolvedComponent>> {
        let keys = ComponentKey::ALL;
        let term = wire::resolve_many_term(
            self.manifest.root_uri(),
            &keys
                .iter()
                .map(|key| key.as_str().to_string())
                .collect::<Vec<_>>(),
            1,
        )?;
        let (value, _meta) = wire::explore_value(&self.inner, &term).await?;
        let values = wire::decode_reply(&value)?;
        let map = values
            .first()
            .and_then(RhoValue::as_map)
            .ok_or_else(|| SdkError::decode("resolveMany", "reply", DecodeKind::WrongType))?;
        let mut resolved = BTreeMap::new();
        for key in keys.iter() {
            let entry = map.get(key.as_str()).ok_or_else(|| {
                SdkError::decode("resolveMany", key.as_str(), DecodeKind::Missing)
            })?;
            let entry = entry.as_map().ok_or_else(|| {
                SdkError::decode("resolveMany", key.as_str(), DecodeKind::WrongType)
            })?;
            let uri = entry
                .get("uri")
                .and_then(RhoValue::as_str)
                .ok_or_else(|| SdkError::decode("resolveMany", "uri", DecodeKind::WrongType))?;
            let version = entry
                .get("version")
                .and_then(RhoValue::as_int)
                .ok_or_else(|| SdkError::decode("resolveMany", "version", DecodeKind::WrongType))?;
            resolved.insert(
                *key,
                ResolvedComponent {
                    uri: uri.to_string(),
                    version,
                },
            );
        }
        for (key, component) in &resolved {
            self.cache_lock().insert(*key, component.clone());
        }
        Ok(resolved)
    }

    pub async fn read(&self, uri: &str, arm: &str, args: &[String]) -> Result<Read<Value>> {
        let term = wire::call_term(uri, arm, args)?;
        let (value, meta) = wire::explore_value(&self.inner, &term).await?;
        Ok(Read {
            value: value.to_json(),
            meta,
        })
    }

    pub async fn read_component(
        &self,
        key: ComponentKey,
        arm: &str,
        args: &[String],
    ) -> Result<Read<Value>> {
        let component = self.resolve(key).await?;
        self.read(&component.uri, arm, args).await
    }

    pub async fn write(&self, uri: &str, arm: &str, args: &[String]) -> Result<Write<Value>> {
        if !self.has_key() {
            return Err(SdkError::NoKey);
        }
        let term = wire::call_term_signed(uri, arm, args)?;
        let receipt = wire::deploy_receipt(&self.inner, &term).await?;
        let value = wire::reply_json(&receipt)?;
        Ok(Write { value, receipt })
    }

    pub async fn write_component(
        &self,
        key: ComponentKey,
        arm: &str,
        args: &[String],
    ) -> Result<Write<Value>> {
        let component = self.resolve(key).await?;
        self.write(&component.uri, arm, args).await
    }

    pub async fn deploy_term(&self, term: &str) -> Result<Write<Value>> {
        if !self.has_key() {
            return Err(SdkError::NoKey);
        }
        let receipt = wire::deploy_receipt(&self.inner, term).await?;
        let value = wire::reply_json(&receipt)?;
        Ok(Write { value, receipt })
    }
}

pub fn parse_resolved(values: &[RhoValue]) -> Result<ResolvedComponent> {
    let uri = values
        .first()
        .and_then(RhoValue::as_str)
        .ok_or_else(|| SdkError::decode("resolve", "uri", DecodeKind::WrongType))?;
    let version = values
        .get(1)
        .and_then(RhoValue::as_int)
        .ok_or_else(|| SdkError::decode("resolve", "version", DecodeKind::WrongType))?;
    Ok(ResolvedComponent {
        uri: uri.to_string(),
        version,
    })
}

fn node_client(node: &str, shard: &str) -> Result<NodeClient> {
    let options = PoolOptions {
        discovery: DiscoveryMode::Disabled,
        shard_id: shard.to_string(),
        ..PoolOptions::default()
    };
    Ok(NodeClient::new_with_options(node, options)?)
}
