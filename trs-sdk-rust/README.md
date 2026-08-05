# trs-sdk-rust

Rust SDK for `trs-node`.

API parity:

- `health()`
- `submit(record)`
- `query(expr)`
- `sync(records)`
- `replay()`

## Example

```rust
use std::time::Duration;
use trs_sdk_rust::TrsClient;

let client = TrsClient::new("http://127.0.0.1:8080", Duration::from_secs(5));
let _health = client.health()?;
# Ok::<(), trs_sdk_rust::TrsError>(())
```

## Live interop flow (against trs-node)

```powershell
cargo run --example interop_node_flow -- http://127.0.0.1:8080 .\interop_rust_flow.json
```
