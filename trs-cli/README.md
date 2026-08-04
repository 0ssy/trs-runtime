# trs-cli

Command-line client for `trs-node` built on `trs-sdk-python`.

## Commands

- `trs health`
- `trs submit --record-json ... | --record-file ...`
- `trs query --expr-json ... | --expr-file ...`
- `trs sync --records-json ... | --records-file ...`
- `trs replay`

## Examples

```bash
trs --url http://127.0.0.1:8080 health
trs submit --record-file .\record.json
trs query --expr-json "{\"type\":\"Intention\"}"
```

