# Overview

## Goal
Deliver a command-line tool that submits a user prompt to multiple AI models, gathers independent answers, runs structured critique rounds, and returns a final consensus response. The process should be deterministic by default, auditable when requested, and configurable without hidden magic.

## Non-Goals (v1)
- Web browsing or tool use by models.
- Long-term memory or personalization.
- Domain-specific compliance or policy enforcement.
- Streaming token-level collaboration.

## Guiding Principles
- Determinism by default: stable output given the same inputs and model configs.
- Explicitness over clever abstractions.
- Small, reviewable changes.
- Clean default output, with verbose audit trails only when requested.

## Assumptions
- Providers expose chat completion APIs.
- A single CLI invocation runs a full consensus cycle and exits.
- Failures for individual models are tolerated when possible.
- The CLI runs without network access unless the user provides credentials and allows it.

## User Stories
- As a user, I can ask a question and receive a consensus answer that explains any key disagreements.
- As a developer, I can add a model provider by implementing a small adapter and config.
- As an operator, I can enable a verbose audit trail for debugging and compliance.

## Success Criteria
- Consensus loop completes in <= 3 rounds for typical prompts.
- Deterministic ordering and aggregation of responses.
- Clear failure messages when consensus cannot be reached.
- Easy to extend to new models.
