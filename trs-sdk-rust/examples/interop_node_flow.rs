use std::env;
use std::fs;
use std::time::Duration;

use serde_json::json;
use trs_sdk_rust::TrsClient;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args();
    let _program = args.next();
    let base_url = args
        .next()
        .ok_or_else(|| "usage: cargo run --example interop_node_flow -- <base_url> <output_path>")?;
    let output_path = args
        .next()
        .ok_or_else(|| "usage: cargo run --example interop_node_flow -- <base_url> <output_path>")?;

    let client = TrsClient::new(base_url.clone(), Duration::from_secs(5));
    let health = client.health()?;

    let observation = json!({
        "id": "rust-obs-1",
        "type": "Observation",
        "author": "rust-sdk",
        "timestamp": "2026-08-05T15:05:00+00:00",
        "schema": "trs.observation.v1",
        "payload": {"subject": "interop", "value": 1},
        "causes": [],
        "authorization": [],
        "signature": "sig:rust-obs-1"
    });
    let submit_result = client.submit(observation)?;

    let intention = json!({
        "id": "rust-int-1",
        "type": "Intention",
        "author": "rust-sdk",
        "timestamp": "2026-08-05T15:05:01+00:00",
        "schema": "trs.intention.v1",
        "payload": {"goal": "interop-check", "horizon": "cycle0012"},
        "causes": ["rust-obs-1"],
        "authorization": [],
        "signature": "sig:rust-int-1"
    });
    let sync_result = client.sync(vec![intention])?;
    let queried = client.query(json!({"author": "rust-sdk"}))?;
    let replay = client.replay()?;
    let unresolved_intentions = replay
        .get("coordination")
        .and_then(|coord| coord.get("unresolved_intentions"))
        .and_then(|raw| raw.as_array())
        .map(|values| values.iter().filter_map(|v| v.as_str().map(ToOwned::to_owned)).collect::<Vec<String>>())
        .unwrap_or_default();

    let summary = json!({
        "sdk": "rust",
        "base_url": base_url,
        "health": {
            "status": health.status,
            "runtime": health.runtime,
            "node": health.node
        },
        "submit": {
            "accepted": submit_result.accepted,
            "record_id": submit_result.record_id,
            "errors": submit_result.errors
        },
        "sync": {
            "accepted_count": sync_result.accepted_count,
            "rejected_count": sync_result.rejected_count,
            "appended_ids": sync_result.appended_ids,
            "rejected_errors": sync_result.rejected_errors
        },
        "query_author_count": queried.len(),
        "replay_unresolved_intentions": unresolved_intentions
    });

    fs::write(output_path, serde_json::to_string_pretty(&summary)?)?;
    println!("{}", serde_json::to_string_pretty(&summary)?);
    Ok(())
}
