# Full protocol: humanize-text

Loaded on demand; see SKILL.md for triggers and core rules.

## Boundary Rules

- Preserve facts, citations, names, dates, numbers, claims, quotes, examples, and user intent.
- Do not invent anecdotes, credentials, sources, study results, personal experience, or domain details.
- Prompt for personal details when the text needs lived specificity that is not present.
- Keep the original certainty level unless the source supports stronger or weaker wording.
- Do not alter code blocks, LaTeX math, blockquotes, footnote anchors, citation markers, or standard reference syntax.
- Do not add deliberate spelling mistakes, invisible characters, formatting tricks, synonym stuffing, or adversarial perturbations.
- Preserve disclosure, attribution, and academic integrity requirements.


---
## Conflict-Aware Style Resolution

Drop or adjust generic humanization tactics when they conflict with the user's target context.

- Academic and scientific text may need hedging, third person, citation density, and formal transitions.
- Corporate, legal, policy, medical, financial, or technical text may need precision more than warmth.
- Personal statements and reflective writing can carry first-person voice, emotion, and uneven rhythm.
- Formal documents should not be forced into contractions, slang, fragments, or chatty asides.
- If a reference style uses em dashes, parentheses, bullets, or symmetry intentionally, preserve its broad pattern without copying unique phrases.
- Preserve requested spelling system, such as US, UK, Canadian, or Vietnamese orthography.

## Workflow

### 1. Lock Meaning

Identify the non-negotiables before rewriting:

- Core thesis or request.
- Factual claims and evidence.
- Names, roles, dates, numbers, citations, and technical terms.
- Required tone and audience expectations.
- Any text that must remain verbatim.

### 2. Diagnose Machine-Like Patterns

Scan for clusters of common LLM tells. Do not mention every minor issue in the final answer unless the user asks for a report.

Style and structure:
- Overly formal, balanced, polished, or symmetrical prose.
- Predictable lists, rule-of-three phrasing, mechanical conclusions, or "not just X, but Y" framing.
- Uniform medium-length sentences with low rhythm variation.
- Repeated paragraph shapes, sentence starters, and transition words.
- Generic positivity, hedging, or both-sides neutrality where a stance is needed.

Vocabulary:
- Inflated words such as delve, tapestry, intricate, foster, bolster, showcase, underscore, vibrant, robust, pivotal, meticulously, align with, garner, interplay.
- Corporate gloss, empty intensifiers, vague abstractions, and notability puffing.
- Nominalization clusters such as utilization, optimization, transformation, characterization, implementation, consideration.
- Complex but generic words where a simpler concrete phrase would do.

Syntax and punctuation:
- Passive voice or noun-heavy clauses that hide the actor.
- Present participial clauses, "that" clauses as subjects, and stacked coordination.
- Excessive em dashes, colons, semicolons, ellipses, rhetorical questions, emojis, Markdown remnants, or decorative bullets.
- Perfect grammar that makes the draft feel sterile when the context calls for a human voice.

Content and formatting:
- Verbosity, filler, hallucinated details, or unsupported claims.
- Low burstiness: every sentence feels equally planned and equally safe.
- Over-attribution, raw metadata, wikitext/Markdown mix, citation artifacts, or database IDs.
- Space-wasting tables, crushed signature gaps, or formatting compromises that look machine-generated.

### 3. Choose Rewrite Intensity

- Light polish: keep structure, fix stiffness, cut filler, smooth rhythm.
- Medium humanization: restructure paragraphs, vary sentence length, replace AI vocabulary, sharpen voice.
- Deep rewrite: rebuild flow and argument while preserving all facts and the user's core intent.

Default to medium unless the source is high-stakes, academic, legal, medical, financial, or citation-heavy. Use light polish for high-stakes text unless the user explicitly asks for deeper restructuring.

### 4. Rewrite For Natural Voice

- Cut padding before adding style.
- Prefer concrete nouns, active verbs, and specific stakes.
- Replace formulaic transitions with natural movement: but, so, also, then, or no transition when the logic is clear.
- Vary sentence length and paragraph rhythm. Mix short, medium, and longer sentences without making the prose chaotic.
- Use contractions, fragments, asides, idioms, or warmth only when they fit the audience.
- Keep a few natural irregularities when they help the voice, such as a short fragment or mild repetition, but do not add errors for disguise.
- Replace generic claims with specific phrasing already supported by the source.
- Convert nominalizations back into verbs when clarity improves.
- Reduce em-dash dependence. Use commas, periods, colons, or parentheses when they read more naturally.
- Keep emotion proportional. A little texture beats theatrical confession.
- Tell stories over lists when the channel calls for personal or persuasive prose.

### 5. Add Specificity Safely

Use the user's existing facts first. If the text needs details that are missing:

- Ask for the detail when it is material and the turn can wait.
- Use placeholders when the structure needs specificity but the fact is unknown.
- Generalize honestly when the user likely cannot or should not provide private details.
- Do not fabricate lived experience, operational failures, grades, publications, credentials, user quotes, or metrics.

Good specificity comes from concrete nouns, real constraints, observable stakes, and sharper causal links. It does not require made-up anecdotes.

### 6. Context Rules

- Academic: preserve citation integrity, formal clarity, hedging, and source-grounded claims. Do not add personal anecdotes unless the assignment calls for reflection.
- Business: make the text direct, useful, and low-friction. Remove buzzwords unless they are terms of art.
- Marketing: keep benefits concrete and credible. Avoid hype the source cannot support.
- Personal: preserve emotional truth and distinctive voice. Do not over-sanitize.
- CV, cover letters, scholarship, and applications: keep claims truthful to the user's actual experience. Remove or flag unsupported achievements.
- Technical writing: preserve terms, code references, APIs, and causal accuracy. Improve flow without weakening precision.
- Vietnamese/English: preserve the requested language and natural register. Keep Vietnamese diacritics.
- Citations and publication lists: strip raw library sequence numbers or accession tags. If a listed paper does not include the candidate as an author, do not present it as their publication; move it to collaborations or contributions when appropriate.
- Credentials: simplify standardized tests to standard ratings, such as "JLPT N1" or "TOEFL 110", without unnecessary test-difficulty padding.
- LaTeX letters: preserve natural signature spacing. Do not crush signature gaps just to force page fitting.

## Detector And Ethics Boundary

Use knowledge of AI-text tells only as a quality diagnostic. Do not optimize for detector scores.

Do not:
- Promise "undetectable" text.
- Run or recommend detector-score loops as acceptance criteria.
- Help conceal plagiarism, evade academic rules, or avoid required AI disclosure.
- Use invisible characters, adversarial formatting, watermark stripping, synonym stuffing, or fake imperfections.

Allowed alternative:
- Offer a truthful rewrite for clarity, rhythm, specificity, voice, citation integrity, and readability.

## Output

For ordinary requests, return the rewritten text first. Add a compact edit note only when useful.

When the user asks for structured output, use:

```yaml
humanize_text_report:
  intent: <audience/channel/voice>
  intensity: <light|medium|deep>
  boundary: readability_only
  tell_audit:
    - <machine-like pattern found>
  changes:
    - <short change category>
  rewritten_text: <final text>
  preserved_facts:
    - <key factual/citation/numeric claims retained>
  risks:
    - <unsupported claims, missing context, ethics/disclosure warning, or none>
```

## Completion Check

- Meaning and factual content are preserved.
- The revision sounds natural for the audience and channel.
- Rhythm has enough variation without sounding forced.
- Cliches, filler, repetition, buzzwords, and inflated claims are reduced.
- Specificity comes from the source text or is clearly requested as a placeholder.
- Any uncertainty, citation, disclosure, or authorship concern is called out briefly.
- No detector-bypass or concealment promise was made.
