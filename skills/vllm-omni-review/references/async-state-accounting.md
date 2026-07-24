# Async State Accounting

Load this reference when a diff changes async/request state, counters, queues,
or lifecycle accounting.

## Required trace

For every changed field, record:

| Field | Semantic unit | Producer | Consumer | Reset/terminal path |
|-------|---------------|----------|----------|---------------------|

Trace all reads and writes in the reviewed class and inherited upstream vLLM
classes. Verify MRO and that producers and consumers use the same unit (for
example, token, output frame, request, block, or queue entry).

Check that stale-output, cancellation, abort, and error guards run before any
accounting mutation. Compare copied or overridden upstream behavior for both
assignments and guard ordering.

## Regression evidence

A helper-only test is insufficient when the changed field has a downstream
consumer. Drive the first consumer with:

1. a stale, cancelled, or error event that exercises the new accounting; and
2. the first valid event afterward, proving it is retained and counters remain
   consistent.

For speculative or batched output, include a multi-item result so token and
frame units cannot be confused.
