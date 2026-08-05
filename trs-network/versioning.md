# Versioning (TRS-NET-1)

## Protocol version header

Clients should send:

- `X-TRS-Protocol-Version: 1`

Servers should return:

- `X-TRS-Protocol-Version: 1`

## Compatibility policy

- Minor additive changes must preserve existing fields/behavior.
- Breaking response/request changes require protocol major increment.
- Implementations must reject unsupported major versions with `400` and a machine-readable code.
