# CLI

`trs-cli` is an operational interface over `trs-sdk-python`.

Examples:

```bash
trs health
trs submit --record-file .\record.json
trs query --expr-json "{\"type\":\"Observation\"}"
trs replay
```

The CLI does not speak runtime internals directly.

