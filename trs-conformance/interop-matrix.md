# Interoperability Matrix

Use this matrix for cross-implementation verification.

## Flows

1. **Submit in A, replay in B**
2. **Submit in A, sync to B, replay in C**
3. **Submit conflict pair in A, verify visibility in B/C**
4. **Submit authorized commitment in A, verify authorization path in B/C**

## Matrix template

| Producer | Consumer | Vector Group | Expected | Result |
| --- | --- | --- | --- | --- |
| Runtime A | Runtime B | valid | pass | pending |
| Runtime A | Runtime B | invalid | pass | pending |
| Runtime A | Runtime B | replay | pass | pending |
| Runtime A | Runtime B | authorization | pass | pending |
| Runtime B | Runtime C | valid | pass | pending |
| Runtime B | Runtime C | invalid | pass | pending |
| Runtime B | Runtime C | replay | pass | pending |
| Runtime B | Runtime C | authorization | pass | pending |

## Classification rules

- **Implementation bug**: one implementation diverges from vector expectations.
- **Specification clarification candidate**: multiple independent implementations diverge in the same way, with no clear contradiction in TRS text.
- **TRS contradiction candidate**: reproducible divergence that cannot be resolved by implementation fix or clarification.
