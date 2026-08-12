# TRS Comparisons

This note answers recurring positioning questions. TRS is complementary to these systems.

## TRS vs W3C PROV-DM

- **PROV-DM**: descriptive provenance data model and interchange vocabulary.
- **TRS**: runtime verification model with explicit authorization/causality/conflict rules over append-only records.

Use PROV-DM for representation/interchange; use TRS when you need executable verification and replay constraints.

## TRS vs UCAN

- **UCAN**: delegated authorization tokens/capabilities.
- **TRS**: full coordination record graph (observations, intentions, commitments) including provenance and replay.

Use UCAN for bearer/delegation token mechanics; use TRS for broader multi-record coordination traceability.

## TRS vs Datomic / XTDB

- **Datomic/XTDB**: immutable/history-preserving databases with temporal query semantics.
- **TRS**: domain-neutral coordination runtime focused on authority chains, causal traceability, and non-silent conflict visibility.

Use Datomic/XTDB as primary data stores; use TRS to model and verify cross-system coordination facts.

## Summary

TRS is not a replacement for provenance vocabularies, capability tokens, or temporal databases.  
TRS is a coordination/provenance verification layer designed to run with them.

