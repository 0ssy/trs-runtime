# trs-openapi

Authoritative network contract for the TRS ecosystem.

- Primary artifact: `openapi.yaml`
- Source of truth for SDK/network interface parity
- Covers:
  - `GET /health`
  - `GET /record/{id}`
  - `POST /submit`
  - `POST /query`
  - `POST /sync`
  - `POST /replay`

`trs-node/openapi/trs-node.openapi.json` is generated from the running node app and should remain wire-compatible with this contract.
