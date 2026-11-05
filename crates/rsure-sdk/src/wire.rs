use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClientConfig {
    pub node: String,
    pub shard_id: String,
    pub manifest: String,
    pub rgen_root_uri: Option<String>,
}

impl Default for ClientConfig {
    fn default() -> Self {
        Self {
            node: "http://localhost:40403".to_owned(),
            shard_id: "/root".to_owned(),
            manifest: "deployments/devnet.json".to_owned(),
            rgen_root_uri: None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReadSource {
    Explore,
    Signed,
}
