//! WASM facade for the r-sure browser wallet and UI.
//!
//! The private key lives only in this module. JS receives the encrypted keystore JSON,
//! public identifiers and JSON envelopes — never a secret.

use rcash_chain::address::eth_address_from_public_key;
use rcash_chain::node::DeployStatus;
use rcash_chain::KeyPair;
use rsure_core::render::render_json;
use rsure_core::{ComponentKey, Manifest};
use rsure_sdk::{Client, ReadMeta, SdkError};
use serde_json::{json, Value};
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[wasm_bindgen]
pub fn classes() -> String {
    rsure_core::RiskClass::ALL
        .iter()
        .map(|class| class.as_str())
        .collect::<Vec<_>>()
        .join(",")
}

#[wasm_bindgen]
pub struct Rsure {
    node: String,
    manifest: Manifest,
    shard: String,
    phlo_limit: i64,
    phlo_price: i64,
    client: Client,
}

#[wasm_bindgen]
impl Rsure {
    #[wasm_bindgen(constructor)]
    pub fn new(node: &str, manifest_json: &str) -> Result<Rsure, JsValue> {
        let manifest = Manifest::from_json(manifest_json).map_err(js)?;
        let client = Client::reader(node, manifest.clone()).map_err(js)?;
        Ok(Self {
            node: node.to_string(),
            manifest,
            shard: Client::DEFAULT_SHARD.to_string(),
            phlo_limit: Client::DEFAULT_PHLO_LIMIT,
            phlo_price: Client::DEFAULT_PHLO_PRICE,
            client,
        })
    }

    pub fn create_wallet(&mut self, password: &str) -> Result<String, JsValue> {
        let key = KeyPair::generate().map_err(js)?;
        let eth = eth_address_from_public_key(key.public_bytes()).map_err(js)?;
        let document = rsure_keystore::encrypt(key.secret_bytes(), &eth, password).map_err(js)?;
        self.rebuild(key)?;
        Ok(document)
    }

    pub fn unlock(&mut self, document: &str, password: &str) -> Result<String, JsValue> {
        let secret = rsure_keystore::decrypt(document, password).map_err(js)?;
        let key = KeyPair::from_secret_bytes(&secret).map_err(js)?;
        let address = key.rev_address().map_err(js)?;
        self.rebuild(key)?;
        Ok(address)
    }

    pub fn lock(&mut self) -> Result<(), JsValue> {
        self.client = Client::reader(&self.node, self.manifest.clone()).map_err(js)?;
        self.client
            .set_network(&self.shard, self.phlo_limit, self.phlo_price);
        Ok(())
    }

    pub fn is_unlocked(&self) -> bool {
        self.client.has_key()
    }

    pub fn address(&self) -> Option<String> {
        self.client.address().ok()
    }

    pub fn public_key(&self) -> Option<String> {
        self.client.key().map(|key| key.public_hex())
    }

    pub fn export_keystore(&self, password: &str) -> Result<String, JsValue> {
        let key = self.client.key().ok_or_else(|| js("wallet is locked"))?;
        let eth = eth_address_from_public_key(key.public_bytes()).map_err(js)?;
        rsure_keystore::encrypt(key.secret_bytes(), &eth, password).map_err(js)
    }

    pub fn set_network(&mut self, shard: &str, phlo_limit: i64, phlo_price: i64) {
        self.shard = shard.to_string();
        self.phlo_limit = phlo_limit;
        self.phlo_price = phlo_price;
        self.client.set_network(shard, phlo_limit, phlo_price);
    }

    pub async fn height(&self) -> Result<String, JsValue> {
        Ok(self.client.height().await.map_err(js)?.to_string())
    }

    pub async fn status(&self) -> Result<String, JsValue> {
        Ok(self.client.status().await.map_err(js)?.to_string())
    }

    pub async fn deploy_status(&self, deploy_id: &str) -> Result<String, JsValue> {
        let status = self.client.deploy_status(deploy_id).await.map_err(js)?;
        Ok(deploy_status_json(deploy_id, &status))
    }

    pub async fn resolve(&self, component: &str) -> String {
        let key = match ComponentKey::parse(component) {
            Some(key) => key,
            None => return error_envelope("unknown-component", component, None),
        };
        match self.client.resolve(key).await {
            Ok(value) => json!({
                "ok": true,
                "key": component,
                "uri": value.uri,
                "version": value.version
            })
            .to_string(),
            Err(error) => sdk_error_envelope(error),
        }
    }

    pub async fn resolve_all(&self) -> String {
        match self.client.resolve_all().await {
            Ok(values) => {
                let mut map = serde_json::Map::new();
                for (key, value) in values {
                    map.insert(
                        key.as_str().to_string(),
                        json!({"uri": value.uri, "version": value.version}),
                    );
                }
                json!({"ok": true, "components": map}).to_string()
            }
            Err(error) => sdk_error_envelope(error),
        }
    }

    pub async fn root_keys(&self) -> String {
        match self
            .client
            .read(self.manifest.root_uri(), "keys", &[])
            .await
        {
            Ok(read) => json!({"ok": true, "data": read.value}).to_string(),
            Err(error) => sdk_error_envelope(error),
        }
    }

    /// A raw read on a component key. `args_json` is a JSON array; an element
    /// `{"raw":"*name"}` is passed through as a Rholang expression.
    pub async fn read_component_json(&self, component: &str, arm: &str, args_json: &str) -> String {
        let key = match ComponentKey::parse(component) {
            Some(key) => key,
            None => return error_envelope("unknown-component", component, None),
        };
        let args = match render_args(args_json) {
            Ok(args) => args,
            Err(error) => return error_envelope("validation", &error, None),
        };
        match self.client.read_component(key, arm, &args).await {
            Ok(read) => read_envelope(read.value, read.meta),
            Err(error) => sdk_error_envelope(error),
        }
    }

    pub async fn read_uri_json(&self, uri: &str, arm: &str, args_json: &str) -> String {
        let args = match render_args(args_json) {
            Ok(args) => args,
            Err(error) => return error_envelope("validation", &error, None),
        };
        match self.client.read(uri, arm, &args).await {
            Ok(read) => read_envelope(read.value, read.meta),
            Err(error) => sdk_error_envelope(error),
        }
    }

    /// A signed write on a component key. `owner_first` prepends `*deployerId`.
    pub async fn write_component_json(
        &self,
        component: &str,
        arm: &str,
        args_json: &str,
        owner_first: bool,
    ) -> String {
        let key = match ComponentKey::parse(component) {
            Some(key) => key,
            None => return error_envelope("unknown-component", component, None),
        };
        let args = match render_args(args_json) {
            Ok(mut args) => {
                if owner_first {
                    args.insert(0, "*deployerId".to_string());
                }
                args
            }
            Err(error) => return error_envelope("validation", &error, None),
        };
        match self.client.write_component(key, arm, &args).await {
            Ok(write) => write_envelope(write.value, write.receipt),
            Err(error) => sdk_error_envelope(error),
        }
    }

    pub async fn write_uri_json(
        &self,
        uri: &str,
        arm: &str,
        args_json: &str,
        owner_first: bool,
    ) -> String {
        let args = match render_args(args_json) {
            Ok(mut args) => {
                if owner_first {
                    args.insert(0, "*deployerId".to_string());
                }
                args
            }
            Err(error) => return error_envelope("validation", &error, None),
        };
        match self.client.write(uri, arm, &args).await {
            Ok(write) => write_envelope(write.value, write.receipt),
            Err(error) => sdk_error_envelope(error),
        }
    }

    pub async fn fund_account_rev(&self, amount: i64) -> String {
        match self.client.fund_account_rev(amount).await {
            Ok(write) => write_envelope(write.value, write.receipt),
            Err(error) => sdk_error_envelope(error),
        }
    }

    pub async fn slip_fund_premium(&self, slip_uri: &str, amount: i64) -> String {
        match self.client.slip_fund_premium(slip_uri, amount).await {
            Ok(write) => write_envelope(write.value, write.receipt),
            Err(error) => sdk_error_envelope(error),
        }
    }

    pub async fn syndicate_contribute(&self, syndicate_uri: &str, amount: i64) -> String {
        match self
            .client
            .syndicate_contribute(syndicate_uri, amount)
            .await
        {
            Ok(write) => write_envelope(write.value, write.receipt),
            Err(error) => sdk_error_envelope(error),
        }
    }

    pub async fn fund_contribute(&self, fund_uri: &str, amount: i64, policy_id: &str) -> String {
        match self
            .client
            .fund_contribute(fund_uri, amount, policy_id)
            .await
        {
            Ok(write) => write_envelope(write.value, write.receipt),
            Err(error) => sdk_error_envelope(error),
        }
    }

    pub async fn faucet(&self, address: &str) -> String {
        match self.client.node().faucet(address).await {
            Ok(value) => json!({"ok": true, "data": value}).to_string(),
            Err(error) => error_envelope("faucet", &error.to_string(), None),
        }
    }

    pub fn sign_payload(&self, payload: &str) -> Result<String, JsValue> {
        let key = self.client.key().ok_or_else(|| js("wallet is locked"))?;
        let digest = rchain_crypto::hash::blake2b256::hash(payload.as_bytes());
        let signature = key.sign_prehash(&digest).map_err(js)?;
        Ok(signature.iter().map(|byte| format!("{byte:02x}")).collect())
    }

    pub fn hash_text(&self, text: &str) -> String {
        let digest = rchain_crypto::hash::blake2b256::hash(text.as_bytes());
        digest.iter().map(|byte| format!("{byte:02x}")).collect()
    }

    pub fn new_op_id(&self, prefix: &str, now_ms: i64) -> Result<String, JsValue> {
        let mut bytes = [0u8; 16];
        getrandom::fill(&mut bytes).map_err(js)?;
        let random: String = bytes.iter().map(|byte| format!("{byte:02x}")).collect();
        Ok(format!("{prefix}-{now_ms}-{random}"))
    }
}

impl Rsure {
    fn rebuild(&mut self, key: KeyPair) -> Result<(), JsValue> {
        let mut client = Client::new(&self.node, self.manifest.clone(), key).map_err(js)?;
        client.set_network(&self.shard, self.phlo_limit, self.phlo_price);
        self.client = client;
        Ok(())
    }
}

fn render_args(args_json: &str) -> Result<Vec<String>, String> {
    let values: Vec<Value> =
        serde_json::from_str(args_json).map_err(|error| format!("args: {error}"))?;
    values
        .into_iter()
        .map(|value| {
            if let Some(raw) = value.get("raw").and_then(Value::as_str) {
                Ok(raw.to_string())
            } else {
                render_json(&value).map_err(|error| error.to_string())
            }
        })
        .collect()
}

fn meta_json(meta: &ReadMeta) -> Value {
    json!({
        "atHeight": meta.at_height,
        "blockHash": meta.block_hash,
        "source": match meta.source {
            rsure_sdk::ReadSource::Explore => "explore",
            rsure_sdk::ReadSource::SignedDeploy => "signedDeploy",
        },
        "deployId": meta.deploy_id,
    })
}

fn read_envelope(data: Value, meta: ReadMeta) -> String {
    json!({"ok": true, "data": data, "read": meta_json(&meta)}).to_string()
}

fn write_envelope(data: Value, receipt: rsure_sdk::DeployReceipt) -> String {
    json!({
        "ok": true,
        "data": data,
        "deploy": {
            "deployId": receipt.deploy_id,
            "finalized": receipt.finalized,
            "blockHash": receipt.block_hash,
            "blockNumber": receipt.block_number,
            "termBytes": receipt.term_bytes,
            "status": receipt.status_text,
        }
    })
    .to_string()
}

fn sdk_error_envelope(error: SdkError) -> String {
    match error {
        SdkError::Refused { reason, code } => json!({
            "ok": false,
            "code": format!("{code:?}"),
            "refusal": reason,
            "message": reason,
        })
        .to_string(),
        other => error_envelope("sdk", &other.to_string(), None),
    }
}

fn error_envelope(code: &str, message: &str, deploy_id: Option<&str>) -> String {
    json!({
        "ok": false,
        "code": code,
        "message": message,
        "deployId": deploy_id,
    })
    .to_string()
}

fn deploy_status_json(deploy_id: &str, status: &DeployStatus) -> String {
    json!({
        "deployId": deploy_id,
        "status": status.status_text(),
        "blockNumber": status.block().map(|block| block.block_number),
        "blockHash": status.block().map(|block| block.block_hash.as_str()),
        "processed": status.is_processed(),
        "success": status.is_success(),
    })
    .to_string()
}

fn js(error: impl std::fmt::Display) -> JsValue {
    JsValue::from_str(&error.to_string())
}
