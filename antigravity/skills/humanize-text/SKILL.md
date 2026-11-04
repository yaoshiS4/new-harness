---
name: humanize-text
description: Humanize, de-robot, polish, or rewrite stiff LLM text for natural voice, readability, and warmth. Not for detector bypass.
---

# Humanize Text

## Purpose

Revise generated, stiff, or over-polished text so it reads clearly, naturally, and specifically while preserving the user's meaning, facts, and authorship constraints. Optimize for better writing, not detector evasion.

If the user asks to bypass AI detectors, make text undetectable, hide AI involvement where disclosure is required, or conceal plagiarism, refuse that goal and offer a readability-focused rewrite instead.

## Inputs

- Source text to revise.
- Audience, channel, use case, and language when available.
- Desired voice, brand tone, author style, or style anchor when provided.
- Constraints such as academic, business, marketing, personal, Vietnamese, English, formal, conversational, short-form, long-form, or publication context.
- Optional intensity: light polish, medium humanization, or deep rewrite.

If key context is missing, infer a conservative default. State the assumption briefly only when it affects the rewrite.

## Full Protocol
Load `references/protocol.md` before executing beyond the core rules above.
