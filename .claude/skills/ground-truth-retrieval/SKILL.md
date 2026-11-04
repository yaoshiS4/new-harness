---
name: ground-truth-retrieval
description: Fetch real-time external ground truth and documentation across GitHub, technical forums, and web pages without hallucination.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Ground-Truth Retrieval Skill (Agent Reach Integration & External Research Scout)

## Purpose
When debugging tricky library errors, compiler faults, or researching recent upstream discussions (GitHub issues/PRs, Reddit discussions, package releases, official docs), agents frequently hallucinate answers or encounter 403 / anti-bot blocks with standard HTTP fetchers.

This skill provides multi-tier ground-truth retrieval:
1. **Tier 1 (Upstream Docs, Native Web & CLI Retrieval)**: Upstream library/framework documentation via `context7` (`mcp__context7__resolve-library-id()` -> `mcp__context7__query-docs()`) as the Step 1 default, followed by native `WebSearch` and `gh-axi` / `curl -sL` via `Bash`.
2. **Tier 2 (Agent-Reach v2 14-Channel CLI & OpenCLI Bridge)**: Unified `agent-reach` v2 runtime across 14 channels (`github`, `twitter`, `reddit`, `youtube`, `bilibili`, `xiaohongshu`, `linkedin`, `boss`, `v2ex`, `xueqiu`, `instagram`, `facebook`, `xiaoyuzhou`, `web`) with deterministic error envelopes, login-wall filtering, site-scoped session reuse, and `jackwener/OpenCLI` browser adapter bridging.
3. **Tier 3 (BrowserOS neo / Session Replay)**: Interactive browser session when full interactive login or DOM manipulation is required.
4. **Tier 4 (Autonomous Literature & Repository Scouting)**: Query arXiv, Semantic Scholar, and GitHub Repositories via `external-research-scout.py` with 7-day local caching and PaperQA2 empirical evidence filtering.

---

## Execution Commands

### Tier 1: Upstream Docs, Native Search & CLI Retrieval (Preferred)
1. **Upstream Library/Framework Documentation (Default Step 1)**:
   Use `context7` via MCP tools (`mcp__<server>__<tool>`) for authoritative, versioned library documentation:
   - Resolve library ID:
     `mcp__context7__resolve-library-id(, Arguments={"libraryName": "<library_name>"})`
   - Query documentation:
     `mcp__context7__query-docs(, Arguments={"libraryId": "<resolved_id>", "query": "<query>"})`
2. **Web Search**:
   Use `WebSearch` with `query: "<QUERY>"` for recent discussions, blog posts, and general web context.
3. **GitHub & Static HTTP Fetch via CLI**:
   - `gh-axi` via `Bash` for repository issues, PRs, and commit diffs.
   - `curl -sL "<URL>"` via `Bash` for raw HTTP fetch of public endpoints.

### Tier 2: Agent-Reach v2 14-Channel CLI & OpenCLI Bridge
Unified v2 CLI across all 14 channels (`github`, `twitter`, `reddit`, `youtube`, `bilibili`, `xiaohongshu`, `linkedin`, `boss`, `v2ex`, `xueqiu`, `instagram`, `facebook`, `xiaoyuzhou`, `web`):

1. **Inspect Available Channels & Actions**:
   ```bash
   ~/.claude/tools/agent-reach/.venv/bin/python -m agent_reach.cli channels
   ```
2. **Execute Channel-Specific Actions**:
   ```bash
   ~/.claude/tools/agent-reach/.venv/bin/python -m agent_reach.cli <channel> <action> [args]
   # Examples:
   ~/.claude/tools/agent-reach/.venv/bin/python -m agent_reach.cli bilibili search "rust async" --limit 5
   ~/.claude/tools/agent-reach/.venv/bin/python -m agent_reach.cli reddit search "tokio runtime" --limit 5
   ~/.claude/tools/agent-reach/.venv/bin/python -m agent_reach.cli twitter thread "<TWEET_URL>"
   ~/.claude/tools/agent-reach/.venv/bin/python -m agent_reach.cli youtube subtitle "<VIDEO_URL>"
   ```
3. **Unified URL Reader & Public-Web Backend**:
   ```bash
   ~/.claude/tools/agent-reach/.venv/bin/python -m agent_reach.cli read "<URL>" [--backend public-web]
   ```
4. **Channel Diagnostics & Media Transcription**:
   ```bash
   ~/.claude/tools/agent-reach/.venv/bin/python -m agent_reach.cli doctor --text
   ~/.claude/tools/agent-reach/.venv/bin/python -m agent_reach.cli transcribe "<URL_OR_FILE>"
   ```
5. **Anti-Bot Protected Page Fallback (Jina Reader)**:
   ```bash
   curl -s "https://r.jina.ai/<URL>"
   ```

#### Deterministic Error Envelope & `FINAL_CODES` Anti-Loop Breaker (`agent_reach/runtime/result.py`)
- **Result Schema**: Every v2 CLI invocation emits `{schema_version, ok, channel, action, backend, items, meta, error}`.
- **Terminal Error Codes (`FINAL_CODES`)**:
  `FINAL_CODES = {NOT_FOUND, BAD_INPUT, PLATFORM_BLOCKED, RATE_LIMITED, NEED_LOGIN, BUSY}`
- **Circuit Breaker Invariant**: On receiving any code in `FINAL_CODES`, **stop immediately**. Never retry the same target with alternative accounts, backends, or browsers; deliver whatever public results have already been gathered.

#### Conservative Login-Wall & Empty-Shell Filter (`agent_reach/runtime/public_web.py`)
- **SPA Shell Rejection**: Automatically reject empty client-side shells where `len(text) < 80` and `text.casefold() == title.casefold()`.
- **Login & Challenge Wall Detection**: Reject responses matching challenge/auth gates (`log in|sign in|join now|登录|登入|注册|just a moment|prove your humanity|access denied|security verification|安全验证|验证码`) instead of polluting context with wall text.

#### Site-Scoped Read-Only Session Reuse & Concurrency Pacing (`agent_reach/runtime/session_reuse.py`)
- **Least-Privilege Cookie Projection**: Project only non-expired domain-scoped cookies (`[name, value, domain, path, secure, httpOnly, sameSite]`). Never read browser passwords, OS keychains, or unrelated domains.
- **Rate & Concurrency Pacing**: Enforce at most **2 concurrent calls per platform**, **4 concurrent calls total**, and **`>=10s` spacing** between same-platform search queries.

#### 3-Tier Capability Honesty Contract (`capabilities.md`)
- **No Shell/Snippet Inflation**: Never treat search snippets, page shells, comment counts, or subtitle track lists as full article bodies or transcripts.
- **No Encoded Field Guessing**: Never guess or hallucinate obfuscated/font-encoded values (e.g., `salary_encoded=true` on job boards).
- **No Fake Multimodal Claims**: Never claim visual/image understanding from text-only social scrapes (e.g., Xiaohongshu or Instagram caption/metadata scrapes).

### Tier 2.5: `jackwener/OpenCLI` Logged-In Browser Adapter Bridge
When `agent-reach` delegates to or pairs with `opencli` for authenticated browser session reuse:
```bash
opencli list search --site <site>
opencli browser open <url> --session research
opencli browser network --static --session research
```
- **JSON Envelope Contract**: `opencli` commands return `{ok, data, error: {code, message, hint}}`. Inspect `ok` and `error.code` before consuming `data`, and honor `FINAL_CODES` on failure.

### Tier 3: BrowserOS Neo Interactive Session
For web applications requiring interactive DOM manipulation or authenticated sessions.

### Tier 4: Autonomous Literature & Repository Scouting (`external-research-scout.py`)
Used during Sleep-Time Meta-Evolution (`auto-harness-healer.py`) or by `meta-evolution` / `research-explorer` subagents when diagnosing systemic failure clusters.

Scout academic literature and open-source repositories for a failure vertex:
```bash
python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/external-research-scout.py --scout --vertex <vertex> --failure-type <failure_type> [--reason "<reason>"]
```

Options:
- `--vertex`: Failure vertex (`hook`, `codebase`, `tool_guidance`, `skill`, `routing`).
- `--failure-type`: Symbolic failure category (e.g. `jev_loop`, `syntax_error`, `read_budget`, `pre_tool_deny`, `gate_block`).
- `--offline`: Bypass remote API calls and instantly retrieve matching canonical blueprints (*Harness²*, *Darwin Gödel Machine*, *AgentSymbolicLearning*, *TextGrad*, *Letta*, *SWE-agent*, *AutoCodeRover*, *AFlow*, *PaperQA2*).
- **Caching**: Results are cached in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/skillbank/research_cache/<sha256>.json` for 7 days (`604,800s`), ensuring `< 5ms` turnaround on repeated queries.
- **Evidence Filter**: Scored using *PaperQA2* empirical evidence indicators; non-empirical marketing or ungrounded blog posts are rejected.

---

## Graceful Fallback Protocol
If `agent-reach` or external APIs encounter a sandbox block, missing browser dependency, network disconnect, or rate limit:
1. Log the failure reason (`needs_validation`).
2. Fallback immediately to `curl -s https://r.jina.ai/<URL>`, `WebSearch`, `curl -sL`, or canonical blueprints in `external-research-scout.py --offline`.
3. Never crash or loop in retry cascades.
