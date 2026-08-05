# Signature Profile (TRS-SIGNATURE-1)

## Algorithm

- Signature scheme: Ed25519.
- Signature form: detached signature encoded as lowercase hex in `record.signature`.

## Signed payload

1. Canonicalize record JSON (full envelope including declared primitive).
2. Compute hash using `TRS-HASH-1`.
3. Domain-separate signing input:

```text
sign_input = ASCII("TRS-SIGNATURE-1\n") || hash_digest_bytes
```

4. Sign `sign_input` with Ed25519 private key.

## Verification order

1. Validate envelope shape and declared primitive schema/payload shape.
2. Recompute canonical bytes and hash.
3. Verify Ed25519 signature over `sign_input`.
4. Then evaluate authorization and causality paths.

## Notes

- `record.signature` must not be interpreted as a semantic field.
- Signature profile version changes require explicit amendment/version update.
