# trs-sdk-go

Go SDK for `trs-node`.

API parity with other SDKs:

- `Health`
- `Submit`
- `Query`
- `Sync`
- `Replay`

## Example

```go
client := trs.NewClient("http://127.0.0.1:8080", 5*time.Second)
health, err := client.Health(context.Background())
```

