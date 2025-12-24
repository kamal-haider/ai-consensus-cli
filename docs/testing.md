# Testing Strategy

## Goals
- Validate consensus loop control flow.
- Ensure deterministic aggregation and ordering.
- Verify CLI argument parsing and config merging.

## Unit Tests
- Consensus criteria logic.
- Digest construction and sorting.
- Change threshold calculation.

## Integration Tests
- Happy-path consensus loop using mocked providers.
- Quorum failure scenario.
- Parse error and recovery behavior.

## Minimal Happy-Path Test (Required)
- Setup: 3 mock participants + 1 mediator.
- Round 1: participants answer.
- Round 2: participants approve.
- Expect: consensus reached and output matches mediator candidate.

## Test Data
- Use fixed fixtures for model outputs.
- Avoid external network calls.

## Command
- pytest

