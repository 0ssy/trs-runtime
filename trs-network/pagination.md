# Pagination

`POST /query` may return large result sets.

Recommended extension profile:

- request fields:
  - `limit` (int > 0)
  - `cursor` (opaque string)
- response fields:
  - `records` (array)
  - `next_cursor` (string or null)

Rules:

- cursor format is server-defined and opaque to clients.
- if `next_cursor` is null, no further pages exist.
- ordering must be deterministic for a fixed store revision.
