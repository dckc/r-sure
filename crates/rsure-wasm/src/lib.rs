use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub struct Rsure {
    node: String,
}

#[wasm_bindgen]
impl Rsure {
    #[wasm_bindgen(constructor)]
    pub fn new(node: String) -> Self {
        Self { node }
    }

    #[wasm_bindgen]
    pub fn node(&self) -> String {
        self.node.clone()
    }

    #[wasm_bindgen]
    pub fn version() -> String {
        env!("CARGO_PKG_VERSION").to_owned()
    }

    #[wasm_bindgen]
    pub fn classes() -> String {
        rsure_core::RiskClass::ALL
            .iter()
            .map(|class| class.as_str())
            .collect::<Vec<_>>()
            .join(",")
    }
}
