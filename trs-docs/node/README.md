# Node

`trs-node` is the network wrapper over `trs-runtime`.

Endpoints:

- `GET /health`
- `POST /submit`
- `POST /query`
- `POST /sync`
- `POST /replay`

It delegates coordination logic to runtime and should not add verifier or business-policy semantics.

