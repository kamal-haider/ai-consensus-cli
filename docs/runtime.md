# Runtime Behavior

## Execution Model
- Single-process CLI.
- Provider calls can be sequential in v1.
- Optional parallel execution can be added later.

## Ordering
- Participants are processed in stable sorted order by name.
- Mediator is always invoked after all participant responses are collected.

## Resource Limits
- Max rounds: default 3.
- Max tokens per model: config-driven.
- Timeout per call: config-driven.
- Max context tokens: config-driven; truncate oldest rounds when near limit (v1).

## Context Limit Behavior (v1)
- If context exceeds `max_context_tokens`, truncate oldest round content first.
- Log a warning event in verbose mode when truncation occurs.

## Determinism Notes
- If parallel execution is introduced, results must be re-sorted before aggregation.
- Any use of randomness must be seeded by config.
