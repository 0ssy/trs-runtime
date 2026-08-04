# Python SDK

`trs-sdk-python` hides HTTP details behind a typed client:

```python
from trs import Client

client = Client("http://127.0.0.1:8080")
client.health()
client.submit(record)
client.query({"type": "Intention"})
client.sync(records)
client.replay()
```

The SDK does not run verifier/replay/graph logic locally.

