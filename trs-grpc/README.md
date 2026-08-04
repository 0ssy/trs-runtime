# trs-grpc

gRPC contract for TRS node parity.

- Primary artifact: `runtime.proto`
- Mirrors the canonical HTTP/OpenAPI surface:
  - `Health`
  - `GetRecord`
  - `Submit`
  - `Query`
  - `Sync`
  - `Replay`

This module is contract-first and language-neutral; server/client generation can be done in any protobuf-supported language.
