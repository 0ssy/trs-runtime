# trs-sdk-typescript

TypeScript SDK for `trs-node`.

API parity with Python SDK:

```ts
const client = new TRSClient("http://127.0.0.1:8080");
await client.submit(record);
await client.query(expr);
await client.sync(records);
await client.replay();
await client.health();
```

