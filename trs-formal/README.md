# trs-formal

Formal-method artifacts for TRS core invariants.

Initial scope:

- append-only behavior,
- causality + authorization closure,
- conflict visibility,
- replay consistency,
- synchronization convergence.

Starter model:

- `tla/TrsCore.tla`
- `tla/TrsCore.cfg`
- Run TLC: `java -cp <path-to-tla2tools.jar> tlc2.TLC -cleanup -deadlock -config TrsCore.cfg TrsCore.tla` (from `trs-formal/tla`)

The model represents two peer logs (`LogA`, `LogB`) with append and sync transitions.
Invariants cover:

- closure in each node,
- non-silent conflict visibility,
- intention closure,
- quiescent convergence.
