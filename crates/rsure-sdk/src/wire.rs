//! Explore/deploy glue and Rholang call templates.

use rcash_chain::node::DeployStatus;
use rcash_chain::rho_expr::{Reply, RhoValue};
use rcash_sdk::Client as RcashClient;
use rsure_core::render::quote_str;
use rsure_core::PROJECT_TERM_BUDGET;
use serde_json::Value;

use crate::error::{DecodeKind, Result, SdkError};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ReadSource {
    Explore,
    SignedDeploy,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ReadMeta {
    pub at_height: i64,
    pub block_hash: String,
    pub source: ReadSource,
    pub deploy_id: Option<String>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct Read<T> {
    pub value: T,
    pub meta: ReadMeta,
}

#[derive(Clone, Debug, PartialEq)]
pub struct Write<T> {
    pub value: T,
    pub receipt: DeployReceipt,
}

#[derive(Clone, Debug, PartialEq)]
pub struct DeployReceipt {
    pub deploy_id: String,
    pub finalized: bool,
    pub block_hash: Option<String>,
    pub block_number: i64,
    pub term_bytes: usize,
    pub status_text: String,
    pub reply: Option<RhoValue>,
}

fn check_size(term: &str) -> Result<()> {
    if term.len() > PROJECT_TERM_BUDGET {
        return Err(SdkError::TermTooLarge {
            bytes: term.len(),
            budget: PROJECT_TERM_BUDGET,
        });
    }
    Ok(())
}

/// Build an explore-term call to a capability.
pub fn call_term(uri: &str, arm: &str, args: &[String]) -> Result<String> {
    let arm = quote_str(arm)?;
    let args = render_args(args);
    let term = format!(
        "new reply, rl(`rho:registry:lookup`), capabilityCh, resultCh in {{ \
         rl!(`{uri}`, *capabilityCh) | \
         for (capability <- capabilityCh) {{ \
         capability!({arm}{args}, *resultCh) | \
         for (@replyValue <- resultCh) {{ reply!(replyValue) }} }} }}"
    );
    check_size(&term)?;
    Ok(term)
}

/// Build a signed call to a capability. The reply goes to `deployId`.
pub fn call_term_signed(uri: &str, arm: &str, args: &[String]) -> Result<String> {
    let arm = quote_str(arm)?;
    let args = render_args(args);
    let term = format!(
        "new rl(`rho:registry:lookup`), capabilityCh, resultCh, \
         deployerId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{ \
         rl!(`{uri}`, *capabilityCh) | \
         for (capability <- capabilityCh) {{ \
         capability!({arm}{args}, *resultCh) | \
         for (@replyValue <- resultCh) {{ deployId!(replyValue) }} }} }}"
    );
    check_size(&term)?;
    Ok(term)
}

/// Build a Root `resolve` read. SureRoot takes `(key, minVersion, ret)`.
pub fn resolve_term(root: &str, key: &str, min_version: i64) -> Result<String> {
    call_term(root, "resolve", &[quote_str(key)?, min_version.to_string()])
}

/// Build a Root `resolveMany` read.
pub fn resolve_many_term(root: &str, keys: &[String], min_version: i64) -> Result<String> {
    let keys = keys
        .iter()
        .map(|key| quote_str(key).map_err(SdkError::from))
        .collect::<Result<Vec<_>>>()?;
    call_term(
        root,
        "resolveMany",
        &[format!("[{}]", keys.join(", ")), min_version.to_string()],
    )
}

fn render_args(args: &[String]) -> String {
    if args.is_empty() {
        String::new()
    } else {
        format!(", {}", args.join(", "))
    }
}

/// Run a public read and decode its value.
pub async fn explore_value(client: &RcashClient, term: &str) -> Result<(RhoValue, ReadMeta)> {
    let response = client.node().explore(term).await?;
    let first = response
        .expr
        .first()
        .ok_or_else(|| SdkError::decode("explore-deploy", "reply", DecodeKind::Missing))?;
    let value = RhoValue::decode(first)?;
    Ok((
        value,
        ReadMeta {
            at_height: response.block.block_number,
            block_hash: response.block.block_hash,
            source: ReadSource::Explore,
            deploy_id: None,
        },
    ))
}

/// Sign, submit and wait for a deploy.
pub async fn deploy_receipt(client: &RcashClient, term: &str) -> Result<DeployReceipt> {
    check_size(term)?;
    let outcome = client.deploy_term(term).await?;
    let status_text = outcome.status.status_text();
    let block_hash = outcome.status.block().map(|block| block.block_hash.clone());
    let block_number = outcome
        .status
        .block()
        .map(|block| block.block_number)
        .unwrap_or_default();
    if !outcome.finalized {
        return Err(SdkError::Unknown {
            deploy_id: outcome.deploy_id,
            last: status_text,
        });
    }
    let reply = match &outcome.status {
        DeployStatus::ProcessedWithSuccess { deploy_result, .. } => {
            deploy_result.first().map(RhoValue::decode).transpose()?
        }
        DeployStatus::ProcessedWithError {
            deploy_error,
            block,
        } => {
            return Err(SdkError::DeployFailed {
                error: deploy_error.clone(),
                block_hash: Some(block.block_hash.clone()),
            })
        }
        DeployStatus::NotProcessed { status } => {
            return Err(SdkError::Unknown {
                deploy_id: outcome.deploy_id,
                last: status.clone(),
            })
        }
    };
    Ok(DeployReceipt {
        deploy_id: outcome.deploy_id,
        finalized: true,
        block_hash,
        block_number,
        term_bytes: term.len(),
        status_text,
        reply,
    })
}

/// Decode the protocol `(true, ...)` / `(false, reason)` convention.
pub fn decode_reply(value: &RhoValue) -> Result<Vec<RhoValue>> {
    match Reply::from_value(value)? {
        Reply::Ok(values) => Ok(values),
        Reply::Refused(reason) => Err(SdkError::refused(reason)),
    }
}

pub fn reply_json(receipt: &DeployReceipt) -> Result<Value> {
    let reply = receipt
        .reply
        .as_ref()
        .ok_or_else(|| SdkError::decode("deploy", "reply", DecodeKind::Missing))?;
    let values = decode_reply(reply)?;
    Ok(Value::Array(values.iter().map(RhoValue::to_json).collect()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn resolve_has_three_arguments() {
        let term = resolve_term("rho:id:abc", "component:clock", 1).unwrap();
        assert!(term.contains("\"resolve\", \"component:clock\", 1"));
    }

    #[test]
    fn explore_replies_on_the_private_name() {
        let term = call_term("rho:id:abc", "info", &[]).unwrap();
        assert!(term.starts_with("new reply,"));
        assert!(!term.contains("deployId"));
    }
}
