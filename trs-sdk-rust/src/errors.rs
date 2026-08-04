use std::fmt::{Display, Formatter};

#[derive(Debug, Clone)]
pub struct TrsValidationError {
    pub message: String,
    pub errors: Vec<String>,
}

#[derive(Debug)]
pub enum TrsError {
    ConnectionError(String),
    ValidationError(TrsValidationError),
    ServerError(String),
    ProtocolError(String),
}

impl Display for TrsError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            TrsError::ConnectionError(message) => write!(f, "{message}"),
            TrsError::ValidationError(err) => write!(f, "{}", err.message),
            TrsError::ServerError(message) => write!(f, "{message}"),
            TrsError::ProtocolError(message) => write!(f, "{message}"),
        }
    }
}

impl std::error::Error for TrsError {}

