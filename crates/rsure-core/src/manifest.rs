//! The r-sure install manifest (`deployments/devnet.json`).
//!
//! The installer writes `{root_uri, components: {file: [[uris]]}}`: each deploy term
//! returns a nested list of registry URIs. The flattener below is the one place that
//! knows the expected URI count and order for a file.

use std::collections::{BTreeMap, BTreeSet};

use serde_json::Value;

use crate::component::ComponentKey;
use crate::error::CoreError;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Manifest {
    root_uri: String,
    components: BTreeMap<String, Vec<String>>,
}

impl Manifest {
    pub fn from_json(document: &str) -> Result<Self, CoreError> {
        let value: Value = serde_json::from_str(document)
            .map_err(|error| CoreError::Manifest(error.to_string()))?;
        let root_uri = value
            .get("root_uri")
            .and_then(Value::as_str)
            .ok_or_else(|| CoreError::Manifest("missing root_uri".into()))?
            .to_owned();
        if !root_uri.starts_with("rho:id:") {
            return Err(CoreError::Manifest("root_uri is not a rho:id URI".into()));
        }

        let components = value
            .get("components")
            .and_then(Value::as_object)
            .ok_or_else(|| CoreError::Manifest("missing components".into()))?;

        let mut flat = BTreeMap::new();
        for (file, entry) in components {
            let uris = flatten(entry);
            if uris.is_empty() {
                return Err(CoreError::Manifest(format!("{file}: no URIs")));
            }
            if !uris.iter().all(|uri| uri.starts_with("rho:id:")) {
                return Err(CoreError::Manifest(format!("{file}: non-rho:id URI")));
            }
            flat.insert(file.clone(), uris);
        }

        let manifest = Self {
            root_uri,
            components: flat,
        };
        manifest.check_shape()?;
        Ok(manifest)
    }

    fn check_shape(&self) -> Result<(), CoreError> {
        let mut seen = BTreeSet::new();
        for key in ComponentKey::ALL {
            let file = key.manifest_file();
            let uris = self
                .components
                .get(file)
                .ok_or_else(|| CoreError::Manifest(format!("missing {file}")))?;
            let index = key.manifest_index();
            if index >= uris.len() {
                return Err(CoreError::Manifest(format!(
                    "{file}: {} has index {index}, only {} URI(s)",
                    key.as_str(),
                    uris.len()
                )));
            }
            let uri = &uris[index];
            if !seen.insert(uri.clone()) {
                return Err(CoreError::Manifest(format!("duplicate URI {uri}")));
            }
        }
        Ok(())
    }

    pub fn root_uri(&self) -> &str {
        &self.root_uri
    }

    pub fn component_uri(&self, key: ComponentKey) -> &str {
        // `check_shape` proved the index exists.
        &self.components[key.manifest_file()][key.manifest_index()]
    }

    pub fn components(&self) -> &BTreeMap<String, Vec<String>> {
        &self.components
    }
}

fn flatten(value: &Value) -> Vec<String> {
    match value {
        Value::String(uri) => vec![uri.clone()],
        Value::Array(items) => items.iter().flat_map(flatten).collect(),
        _ => Vec::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const DOCUMENT: &str = r#"{
      "root_uri": "rho:id:root",
      "components": {
        "01_kernel.rho": [["rho:id:c", "rho:id:v", "rho:id:k"]],
        "02_admin.rho": [["rho:id:g", "rho:id:a"]],
        "03_terms.rho": [["rho:id:t"]],
        "04_math.rho": [["rho:id:m"]],
        "05_rgen.rho": [["rho:id:r"]],
        "40_payments.rho": [["rho:id:p"]],
        "15_distribution.rho": [["rho:id:d"]],
        "16_fund.rho": [["rho:id:f"]],
        "10_syndicate.rho": [["rho:id:s"]],
        "11_broker.rho": [["rho:id:b"]],
        "12_risk.rho": [["rho:id:ri"]],
        "13_slip.rho": [["rho:id:sl"]],
        "14_line.rho": [["rho:id:l"]],
        "17_policy.rho": [["rho:id:po"]],
        "18_claim.rho": [["rho:id:cl"]],
        "19_books.rho": [["rho:id:pb", "rho:id:cb"]]
      }
    }"#;

    #[test]
    fn maps_every_component() {
        let manifest = Manifest::from_json(DOCUMENT).unwrap();
        assert_eq!(manifest.root_uri(), "rho:id:root");
        assert_eq!(manifest.component_uri(ComponentKey::Clock), "rho:id:c");
        assert_eq!(manifest.component_uri(ComponentKey::ClaimBook), "rho:id:cb");
    }

    #[test]
    fn rejects_a_missing_component() {
        let broken = DOCUMENT.replace("\"19_books.rho\": [[\"rho:id:pb\", \"rho:id:cb\"]]", "");
        assert!(Manifest::from_json(&broken).is_err());
    }
}
