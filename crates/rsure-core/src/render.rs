use serde_json::Value;

use crate::error::CoreError;

/// Quote a JSON string for Rholang. Refuses newlines and control characters.
pub fn quote_str(value: &str) -> Result<String, CoreError> {
    if value.chars().any(|c| c.is_control()) {
        return Err(CoreError::Render);
    }
    Ok(format!(
        "\"{}\"",
        value.replace('\\', "\\\\").replace('"', "\\\"")
    ))
}

/// Render a non-negative integer that fits in an i64.
pub fn render_i64(value: u64) -> Result<String, CoreError> {
    if value > i64::MAX as u64 {
        return Err(CoreError::Render);
    }
    Ok(value.to_string())
}

/// Render a JSON value; floats are refused.
pub fn render_json(value: &Value) -> Result<String, CoreError> {
    match value {
        Value::Null => Ok("Nil".to_owned()),
        Value::Bool(flag) => Ok(if *flag { "true" } else { "false" }.to_owned()),
        Value::Number(number) => {
            if let Some(value) = number.as_u64() {
                render_i64(value)
            } else if let Some(value) = number.as_i64() {
                if value < 0 {
                    Err(CoreError::Render)
                } else {
                    Ok(value.to_string())
                }
            } else {
                Err(CoreError::Render)
            }
        }
        Value::String(text) => quote_str(text),
        Value::Array(items) => {
            let mut out = String::from("[");
            for (index, item) in items.iter().enumerate() {
                if index > 0 {
                    out.push_str(", ");
                }
                out.push_str(&render_json(item)?);
            }
            out.push(']');
            Ok(out)
        }
        Value::Object(map) => {
            let mut out = String::from("{");
            for (index, (key, item)) in map.iter().enumerate() {
                if index > 0 {
                    out.push_str(", ");
                }
                out.push_str(&quote_str(key)?);
                out.push_str(": ");
                out.push_str(&render_json(item)?);
            }
            out.push('}');
            Ok(out)
        }
    }
}
