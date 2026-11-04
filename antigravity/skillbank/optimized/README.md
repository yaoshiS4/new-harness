# SkillBank Optimized Layer

## Purpose
Store the current best validated version of trainable skill documents.

Use this layer when a skill has passed SkillOpt review and should be preferred over the raw skillbank entry during harness activation or dreaming consolidation.

## Layout

- `optimized/<skill-id>/best_skill.md`: current best validated skill text.
- `optimized/<skill-id>/manifest.yaml`: validation metadata, edit budget, and promotion state.
- `optimized/<skill-id>/history/`: optional local notes for promoted or rejected variants if a human reviewer wants them on disk.

## Promotion Rules

1. Only validated, Oracle-reviewed edits may replace `best_skill.md`.
2. Candidate edits are bounded by a small textual budget, defaulting to 3 operations or 20 percent changed lines per epoch, whichever is smaller.
3. Rejected edits belong in `codex_knowledge` memory or graph stores unless a reviewed lesson is explicitly promoted into SkillBank.
4. Task agents should consult this layer before falling back to raw skillbank text.
