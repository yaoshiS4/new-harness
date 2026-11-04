# Clarify Gate

Alias of `preflight_gate` with SOL clarification semantics.

## Purpose
Ensure the request is understood before exploration or implementation begins.

## Gate Check
1. User intent is explicit.
2. All nouns have clear referents.
3. Success criteria are measurable.
4. Constraints are stated or marked as unknown.
5. Remaining ambiguity is handled with a BreakRequest.

## Exit Criteria
- Task contract emitted in Markdown or YAML.
- No unresolved ambiguity that changes scope.
