# Hashing Profile (TRS-HASH-1)

## Input

Input is the canonical UTF-8 JSON byte string from `canonical-json.md`.

## Algorithm

- Hash function: SHA-256.
- Digest output:
  - binary form for cryptographic operations;
  - lowercase hex form for human/readable test vectors.

## Domain separation

For hash derivation used in signatures:

```text
hash_input = ASCII("TRS-HASH-1\n") || canonical_record_bytes
digest = SHA256(hash_input)
```

## Determinism requirement

Two conforming implementations MUST produce identical digest bytes for the same logical record.
