# CYCLE-0014 Threat Model Draft

## Scope

- Record authenticity and signature verification path
- Key generation and rotation handling
- Delegation chain abuse and forged authorization attempts
- Record tampering and replayed malicious payloads

## Assets

- Signing private keys
- Registered public keys
- Delegation relationships
- Append-only record history

## Threats

- Key theft or unauthorized key registration
- Signature forgery attempts
- Delegation escalation (non-approved transitivity)
- Malicious payload tampering after signature issuance

## Controls in current baseline

- Ed25519 signatures in `runtime.crypto.CryptoSuite`
- Signature verification in `Verifier.verify_signature`
- Delegation checks in authorization traceability path
- Attack tests for forged authorization and payload abuse

## External audit focus

- Key management lifecycle procedures
- Cryptographic misuse opportunities
- Verification bypass potential
- Operational controls around key custody and rotation
