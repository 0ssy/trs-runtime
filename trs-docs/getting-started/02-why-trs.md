# Why TRS was created

Distributed coordination often fails because systems hide conflict, overwrite state, or depend on centralized online authorities.

TRS addresses this by:

- preserving append-only history,
- exposing conflict instead of silently dropping it,
- enabling local verification and replay,
- separating coordination infrastructure from application policy.

