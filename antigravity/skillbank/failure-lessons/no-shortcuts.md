```yaml
skillbank_entry:
  id: failure-no-shortcuts-verification
  layer: failure-lessons
  status: active
  source_evidence:
    - user no-shortcuts verification requirement
  activation_triggers:
    - final-review
    - harness-change
    - workflow-change
  adherence_checks:
    - no empty-shell files
    - no tool names lacking config or implementation
    - validation claims include command evidence
  last_reviewed: 2026-06-03
```

# No-Shortcuts Verification

Before completion, search for empty-shell language, tool names lacking implementation, cross-runtime path coupling, and validation claims without evidence. Report every failed command plainly.
