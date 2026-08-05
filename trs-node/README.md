# trs-node

Network service wrapper for `trs-runtime`. This project exposes runtime operations over HTTP and does not reimplement verifier, graph, replay, or storage logic.

## Endpoints

- `GET /health`
- `GET /record/{id}`
- `POST /submit`
- `POST /query`
- `POST /sync`
- `POST /replay`
- `GET /openapi.json`

Published OpenAPI artifact:

- `openapi/trs-node.openapi.json`
- `../trs-openapi/openapi.yaml` (authoritative ecosystem contract)

## Run

```bash
# In-memory mode
python -m node.app serve

# Deployable persistent profile
python -m node.app serve --db .\data\trs-node.db

# If installed as a package script
trs-node serve --db .\data\trs-node.db
```

## Test

```bash
python -m unittest discover -s trs-node/tests -t trs-node -p test_*.py -v
```
