use std::time::Duration;

use reqwest::Method;
use reqwest::blocking::Client;
use serde_json::{Value, json};

use crate::errors::{TrsError, TrsValidationError};
use crate::models::{HealthStatus, SubmitResult, SyncResult};

pub struct TrsClient {
    base_url: String,
    client: Client,
}

impl TrsClient {
    pub fn new(base_url: impl Into<String>, timeout: Duration) -> Self {
        let normalized = base_url.into().trim_end_matches('/').to_string();
        let client = Client::builder()
            .timeout(timeout)
            .build()
            .unwrap_or_else(|_| Client::new());
        Self {
            base_url: normalized,
            client,
        }
    }

    pub fn health(&self) -> Result<HealthStatus, TrsError> {
        let payload = self.send(Method::GET, "/health", None)?;
        serde_json::from_value::<HealthStatus>(payload)
            .map_err(|err| TrsError::ProtocolError(format!("health response must be an object: {err}")))
    }

    pub fn submit(&self, record: Value) -> Result<SubmitResult, TrsError> {
        if !record.is_object() {
            return Err(TrsError::ProtocolError(
                "record must be a JSON object".to_string(),
            ));
        }
        let payload = self.send(Method::POST, "/submit", Some(json!({ "record": record })))?;
        let result: SubmitResult = serde_json::from_value(payload)
            .map_err(|err| TrsError::ProtocolError(format!("submit response must be an object: {err}")))?;
        if !result.accepted {
            return Err(TrsError::ValidationError(TrsValidationError {
                message: "record rejected by verifier".to_string(),
                errors: result.errors.clone(),
            }));
        }
        Ok(result)
    }

    pub fn query(&self, expr: Value) -> Result<Vec<Value>, TrsError> {
        if !expr.is_object() {
            return Err(TrsError::ProtocolError(
                "expr must be a JSON object".to_string(),
            ));
        }
        let payload = self.send(Method::POST, "/query", Some(json!({ "query": expr })))?;
        let records = payload
            .get("records")
            .ok_or_else(|| TrsError::ProtocolError("records must be an array".to_string()))?;
        let arr = records
            .as_array()
            .ok_or_else(|| TrsError::ProtocolError("records must be an array".to_string()))?;
        let mut out = Vec::with_capacity(arr.len());
        for item in arr {
            if !item.is_object() {
                return Err(TrsError::ProtocolError("record must be an object".to_string()));
            }
            out.push(item.clone());
        }
        Ok(out)
    }

    pub fn sync(&self, records: Vec<Value>) -> Result<SyncResult, TrsError> {
        if records.iter().any(|record| !record.is_object()) {
            return Err(TrsError::ProtocolError(
                "all records must be JSON objects".to_string(),
            ));
        }
        let payload = self.send(Method::POST, "/sync", Some(json!({ "records": records })))?;
        serde_json::from_value::<SyncResult>(payload)
            .map_err(|err| TrsError::ProtocolError(format!("sync response must be an object: {err}")))
    }

    pub fn replay(&self) -> Result<Value, TrsError> {
        let payload = self.send(Method::POST, "/replay", Some(json!({})))?;
        if !payload.is_object() {
            return Err(TrsError::ProtocolError(
                "replay response must be an object".to_string(),
            ));
        }
        Ok(payload)
    }

    fn send(&self, method: Method, path: &str, body: Option<Value>) -> Result<Value, TrsError> {
        let url = format!("{}{}", self.base_url, path);
        let mut req = self.client.request(method, &url).header("Accept", "application/json");
        if let Some(payload) = body {
            req = req.json(&payload);
        }

        let response = req
            .send()
            .map_err(|err| TrsError::ConnectionError(err.to_string()))?;

        let status = response.status();
        let raw = response
            .text()
            .map_err(|err| TrsError::ConnectionError(err.to_string()))?;

        let payload = if raw.trim().is_empty() {
            json!({})
        } else {
            serde_json::from_str::<Value>(&raw)
                .map_err(|_| TrsError::ProtocolError("invalid JSON response from trs-node".to_string()))?
        };

        if status.is_success() {
            return Ok(payload);
        }

        let message = extract_error_message(&payload, status.as_u16());
        if status.is_client_error() {
            return Err(TrsError::ValidationError(TrsValidationError {
                message,
                errors: Vec::new(),
            }));
        }
        Err(TrsError::ServerError(message))
    }
}

fn extract_error_message(payload: &Value, status: u16) -> String {
    if let Some(detail) = payload.get("detail").and_then(Value::as_str) {
        if !detail.is_empty() {
            return detail.to_string();
        }
    }
    if let Some(error) = payload.get("error").and_then(Value::as_str) {
        if !error.is_empty() {
            return error.to_string();
        }
    }
    format!("http {status}")
}

