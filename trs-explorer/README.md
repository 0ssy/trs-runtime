# trs-explorer

Visual browser for TRS records, graph relationships, replay timeline, and verifier explanations.

Architecture:

`Explorer -> trs-sdk-python -> trs-node -> trs-runtime`

No runtime imports are used in this repository.

## Features (v0.1)

- Record graph listing (nodes + edges)
- Record navigation (parents, children, authorization)
- Replay timeline view
- Search (`subject`, `author`, `primitive`, `schema`, `record`, `status`)
- Explainability panel for validation outcomes

## Run

```bash
python -m trs_explorer.app
```

Then open: `http://127.0.0.1:8090`

