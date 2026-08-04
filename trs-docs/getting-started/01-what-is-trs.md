# What is TRS?

TRS is a coordination runtime built on immutable records.

Each record declares a primitive in its envelope:

- `Observation`
- `Commitment`
- `Intention`

The verifier checks whether payload structure is valid for the declared primitive. TRS does not infer ontology from payload content.

