use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

use serde_json::{Value, json};
use trs_sdk_rust::{TrsClient, TrsError};

#[test]
fn health_submit_query_sync_replay_flow() {
    let state = Arc::new(Mutex::new(Vec::<Value>::new()));
    let server = TestServer::spawn(0, state.clone());
    let client = TrsClient::new(server.base_url(), Duration::from_secs(2));

    let health = client.health().expect("health");
    assert_eq!(health.status, "ok");

    client
        .submit(json!({"id":"g1","type":"Observation","payload":{"subject":"boot","value":1}}))
        .expect("submit");
    let rows = client.query(json!({})).expect("query");
    assert_eq!(rows.len(), 1);
    let sync = client.sync(rows).expect("sync");
    assert_eq!(sync.accepted_count, 1);
    let replay = client.replay().expect("replay");
    assert!(replay.get("coordination").is_some());
}

#[test]
fn submit_invalid_returns_validation_error() {
    let state = Arc::new(Mutex::new(Vec::<Value>::new()));
    let server = TestServer::spawn(0, state);
    let client = TrsClient::new(server.base_url(), Duration::from_secs(2));
    let result = client.submit(json!({"id":"bad","type":"Observation","payload":{}}));
    match result {
        Err(TrsError::ValidationError(_)) => {}
        other => panic!("expected validation error, got {other:?}"),
    }
}

#[test]
fn timeout_returns_connection_error() {
    let state = Arc::new(Mutex::new(Vec::<Value>::new()));
    let server = TestServer::spawn(250, state);
    let client = TrsClient::new(server.base_url(), Duration::from_millis(20));
    let result = client.health();
    match result {
        Err(TrsError::ConnectionError(_)) => {}
        other => panic!("expected connection error, got {other:?}"),
    }
}

struct TestServer {
    base_url: String,
}

impl TestServer {
    fn spawn(delay_ms: u64, records: Arc<Mutex<Vec<Value>>>) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("bind listener");
        let addr = listener.local_addr().expect("local addr");
        thread::spawn(move || {
            for incoming in listener.incoming() {
                match incoming {
                    Ok(mut stream) => {
                        let records = records.clone();
                        thread::spawn(move || handle_connection(&mut stream, delay_ms, records));
                    }
                    Err(_) => break,
                }
            }
        });
        Self {
            base_url: format!("http://{}", addr),
        }
    }

    fn base_url(&self) -> String {
        self.base_url.clone()
    }
}

fn handle_connection(stream: &mut TcpStream, delay_ms: u64, records: Arc<Mutex<Vec<Value>>>) {
    if delay_ms > 0 {
        thread::sleep(Duration::from_millis(delay_ms));
    }

    let mut buf = vec![0_u8; 65536];
    let n = stream.read(&mut buf).unwrap_or(0);
    if n == 0 {
        return;
    }
    let request = String::from_utf8_lossy(&buf[..n]).to_string();
    let mut lines = request.split("\r\n");
    let start = lines.next().unwrap_or("");
    let mut content_length = 0_usize;
    for line in request.split("\r\n") {
        let lower = line.to_lowercase();
        if lower.starts_with("content-length:") {
            content_length = lower["content-length:".len()..].trim().parse::<usize>().unwrap_or(0);
        }
    }

    let body = if let Some(split) = request.find("\r\n\r\n") {
        let raw = &request[(split + 4)..];
        if raw.len() >= content_length {
            raw[..content_length].to_string()
        } else {
            raw.to_string()
        }
    } else {
        String::new()
    };

    let response_body = route(start, body, records);
    let payload = response_body.to_string();
    let response = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        payload.len(),
        payload
    );
    let _ = stream.write_all(response.as_bytes());
    let _ = stream.flush();
}

fn route(start_line: &str, body: String, records: Arc<Mutex<Vec<Value>>>) -> Value {
    if start_line.starts_with("GET /health") {
        return json!({"status":"ok","runtime":"1.0.0","node":"0.1.0"});
    }
    if start_line.starts_with("POST /submit") {
        let parsed: Value = serde_json::from_str(&body).unwrap_or_else(|_| json!({}));
        let record = parsed.get("record").cloned().unwrap_or_else(|| json!({}));
        let payload = record.get("payload").cloned().unwrap_or_else(|| json!({}));
        let valid = payload.get("subject").is_some() || payload.get("goal").is_some() || payload.get("action").is_some();
        let rid = record.get("id").and_then(Value::as_str).unwrap_or("").to_string();
        if !valid {
            return json!({"accepted":false,"record_id":rid,"errors":["5.3 Payload Shape"]});
        }
        records.lock().expect("records lock").push(record);
        return json!({"accepted":true,"record_id":rid,"errors":[]});
    }
    if start_line.starts_with("POST /query") {
        let rows = records.lock().expect("records lock").clone();
        return json!({"records": rows});
    }
    if start_line.starts_with("POST /sync") {
        let parsed: Value = serde_json::from_str(&body).unwrap_or_else(|_| json!({}));
        let rows = parsed.get("records").and_then(Value::as_array).cloned().unwrap_or_default();
        return json!({"accepted_count": rows.len(), "rejected_count": 0, "appended_ids": ["g1"], "rejected_errors": []});
    }
    if start_line.starts_with("POST /replay") {
        return json!({"coordination":{"unresolved_intentions":[]}});
    }
    json!({"error":"not found"})
}

