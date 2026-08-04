# trs-sdk-python

Thin Python client for `trs-node`.

## Install

```bash
pip install -e .
```

## Usage

```python
from trs import Client

client = Client("http://localhost:8080")
health = client.health()
```

## Public API

- `client.health()`
- `client.submit(record)`
- `client.query(expression)`
- `client.sync(records)`
- `client.replay()`

The SDK does not implement verification, replay, graph logic, or payload interpretation.

