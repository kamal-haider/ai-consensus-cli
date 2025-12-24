# Consensus Algorithm

## Criteria
Consensus is reached when both of the following hold:
- approvals >= ceil(2/3 * participants)
- critical_objections == 0

## Stop Conditions
- Max rounds reached (default: 3 total rounds).
- Early stop if candidate changes below threshold.
- Early stop if no changes proposed by any participant.

## Change Threshold
- Use a deterministic diff metric.
- Recommended: normalized Levenshtein distance on whitespace-tokenized text (split on `\\s+`).
- Default threshold: < 10% change.

## Disagreement Summary
If consensus is not reached, include:
- Top 3 unresolved objections.
- Any remaining missing items.
- A short note explaining why consensus failed.

## Scoring (Optional, v1 default off)
- Weighted approvals by model weight.
- Weighted objection severity.

## Edge Cases
- If a participant fails to respond, proceed if quorum is met.
- If quorum not met, abort with a clear error.

## Quorum
- Default quorum: ceil(2/3 * participants).
- Configured participants must be >= 2.
- Quorum behavior is configurable.

## Critical Objections
- A critical objection is one that indicates factual error or potential harm, as defined in prompt criteria.
