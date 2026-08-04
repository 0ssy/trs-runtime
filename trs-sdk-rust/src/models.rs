use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthStatus {
    pub status: String,
    pub runtime: String,
    pub node: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubmitResult {
    pub accepted: bool,
    pub record_id: String,
    pub errors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncResult {
    pub accepted_count: i64,
    pub rejected_count: i64,
    pub appended_ids: Vec<String>,
    pub rejected_errors: Vec<Vec<String>>,
}

