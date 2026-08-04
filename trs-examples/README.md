# trs-examples

Small, runnable reference applications showing how to build with TRS.

## Prerequisites

1. Start `trs-node` on port `8080`:

```bash
python -m node.app
```

2. Run examples from repository root:

```bash
python trs-examples\hello-world\main.py
python trs-examples\todo-list\main.py
python trs-examples\identity\main.py
python trs-examples\inventory\main.py
python trs-examples\contracts\main.py
```

If your node is on another URL:

```bash
set TRS_NODE_URL=http://127.0.0.1:8080
```

## Examples

- `hello-world`: submit a first observation record.
- `todo-list`: model tasks as intentions and completion as commitments.
- `identity`: register and attest a decentralized identity.
- `inventory`: represent scarcity and allocations.
- `contracts`: model offer + acceptance as immutable commitments.
