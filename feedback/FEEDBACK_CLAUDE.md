# Feedback (Claude)

This document tracks Claude's active questions, comments, and concerns. Resolved items are removed to keep this file focused.

---

## Latest

### Architecture Pivot - Simple Query Tool

The project has pivoted from a complex multi-round consensus protocol to a simple query tool.

**New Design:**
- Tool does ONE thing: send a prompt to a model, return the response
- The calling agent (Claude/GPT/etc.) handles synthesis
- No consensus logic, no multi-round dialogue, no mediator

**Key Files Updated:**
- `spec.md` - Rewritten for simple query interface
- `CLAUDE.md` - Updated project overview
- `docs/README.md` - Marked consensus docs as archived
- `docs/providers.md` - Simplified provider interface
- `docs/errors.md` - Simplified error handling
- `docs/testing.md` - Simplified test strategy

**Pending Code Changes:**
The existing implementation in `src/aicx/` contains the full consensus protocol. This will need to be replaced with the simpler query implementation. Key changes needed:

1. Remove consensus logic (`src/aicx/consensus/`)
2. Remove context budget management (`src/aicx/context/`)
3. Remove retry wrapper complexity (`src/aicx/retry/`)
4. Simplify providers to just return text responses
5. Simplify CLI to `aicx query "prompt" --model <model>`
6. Update tests to match new design

---

## Previous

*Previous feedback from consensus protocol implementation has been archived.*
