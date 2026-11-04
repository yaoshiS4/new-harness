---
name: axi-tools
description: Token-efficient AXI CLI tools (gh-axi, chrome-devtools-axi, firefox-axi, agy-axi) returning compact TOON output.
---

# AXI Tools (Agent eXperience Interface)

AXI tools are command-line utilities built specifically for AI agents, following the **10 AXI Principles** (https://axi.md). They emit **TOON** (Token-Oriented Object Notation) on `stdout`, delivering structured data with ~40% fewer tokens than JSON while avoiding verbose manuals, unbounded lists, and hallucinated follow-up calls.

## Core Architectural Invariants

1. **TOON Output**: Compact tabular output headers (`name[N]{field1,field2}:`), minimal schemas (3-4 fields), and pre-computed aggregates.
2. **Read-Only / Safe Execution**: Zero destructive side-effects on read/inspect commands; mutations require explicit parameters.
3. **Structured Errors & Predictable Exits**: Exit code 0 for success/no-op, 1 for runtime error, 2 for usage/flag error. All errors print actionable fixes on `stdout`.
4. **Contextual Next-Step Disclosure**: Every command concludes with a `help[N]:` block suggesting 2-4 exact parameterized commands.

---

## 1. `agy-axi` — Antigravity Session & Telemetry Inspector

### Live 0-Arg Workspace & Session Snapshot
```bash
agy-axi
```
Returns active Antigravity session ID, title, status, context token breakdown (`input`, `output`, `cache_read`), provider quota fractions, git diff aggregates (`+ins/-del`), and active subagent states.

### SQLite Database Inspector
```bash
# List all tables, row counts, and column counts in TOON
agy-axi db ~/.gemini/antigravity-cli/conversation_summaries.db

# Run safe read-only SELECT query (capped at 10 rows by default)
agy-axi db ~/.gemini/antigravity-cli/conversation_summaries.db "SELECT conversation_id, title, step_count FROM conversation_summaries ORDER BY last_modified_time DESC LIMIT 5"

# Lift truncation and display full rows
agy-axi db ~/.gemini/antigravity-cli/conversation_summaries.db "SELECT * FROM conversation_summaries LIMIT 20" --full
```

### Git Repository Aggregates
```bash
# Pre-computed branch, worktrees, dirty file count, +ins/-del diff, and recent 5 commits
agy-axi git

# Show up to 20 recent commits and full diff aggregates
agy-axi git --full
```

### Transcript & Step Error Tracing
```bash
# Recent 5 steps and error traces of active conversation
agy-axi logs

# Target specific conversation transcript with full steps
agy-axi logs aa8631d7-a9c8-4c3e-9aa0-63d171c15a43 --full
```

---

## 2. `gh-axi` — GitHub CLI Ergonomics

Compact TOON wrapper around GitHub CLI with command-first targeting and zero context bloat.

```bash
# List open issues for a repository
gh-axi issue list -R owner/repo

# View pull requests with CI check status
gh-axi pr list -R owner/repo
gh-axi pr view 42 -R owner/repo

# List workflow runs and checks
gh-axi run list -R owner/repo

# View repository metadata
gh-axi repo view --repo owner/repo

# Search issues or code
gh-axi search issues "memory leak" --repo owner/repo
```

---

## 3. `sqlite-axi` — High-Performance SQLite Exploration

```bash
# Inspect all tables, row counts, and column counts
sqlite-axi tables <database-path>

# Inspect columns, data types, indexes, and foreign keys of a table
sqlite-axi schema <database-path> <table-name>

# Sample first 10 rows of a table
sqlite-axi sample <database-path> <table-name> --limit 10

# Execute safe, read-only SELECT query
sqlite-axi query <database-path> "SELECT * FROM <table-name> LIMIT 25"
```

---

## 4. `quota-axi` — Agent Provider Quotas & Runway

```bash
# Live quota window fractions (Gemini, Claude, Codex, Copilot)
quota-axi

# Full quota evidence including countdowns, window IDs, and pacing
quota-axi --full
```

---

## 5. `chrome-devtools-axi` — Browser Automation & Scraping

```bash
# Navigate to URL
chrome-devtools-axi open https://example.com

# Dump accessible DOM tree snapshot in TOON
chrome-devtools-axi snapshot

# Click element by UID
chrome-devtools-axi click @e12

# Fill form field by UID
chrome-devtools-axi fill @e14 "search query"

# Take screenshot
chrome-devtools-axi screenshot /tmp/capture.png
```

---

## 6. `firefox-axi` — Native Firefox Marionette CLI Controller

Zero-dependency Python 3 controller speaking Firefox Marionette wire protocol v3 directly (`127.0.0.1:2828` live user profile, automatic fallback to persistent headless profile at `~/.cache/firefox-axi/profile` on port `2829`).

```bash
# Check Marionette connection status (live 2828 vs managed 2829)
firefox-axi

# Navigate to URL (auto-starts managed Firefox on 2829 if needed)
firefox-axi open https://example.com

# Tag visible interactive/semantic elements with @eN UIDs and dump TOON snapshot
firefox-axi snapshot
firefox-axi snapshot --full

# Interact with elements by @eN UID or CSS selector
firefox-axi click @e1
firefox-axi fill @e2 "search query"
firefox-axi press Enter

# Execute JS in page content context or privileged Firefox chrome context
firefox-axi eval "document.title"
firefox-axi chrome-eval "Services.appinfo.version"

# Manage tabs and capture screenshots
firefox-axi tabs
firefox-axi newtab https://example.org
firefox-axi selecttab 0
firefox-axi closetab 1
firefox-axi screenshot /tmp/ff-test.png

# Explicitly start or stop managed Firefox instance
firefox-axi start --headed
firefox-axi stop
```

---

## 7. `npm-axi` — NPM Package & Dependency Search

```bash
# Search npm registry with compact name, version, description
npm-axi search "ripgrep" --limit 10

# Inspect package details
npm-axi view <package-name>
```

---

## 8. `adb-axi` — Android Debugging & App Lifecycle

```bash
# List connected devices, API level, form factor, and state
adb-axi devices

# Run diagnostics on host, adb server, and connected target
adb-axi doctor

# App lifecycle and crash logs
adb-axi app list
adb-axi logcat --errors-only
```

---

## 9. `axi-axi` — Meta-Validator & Spec Compliance

```bash
# Inspect the 10 AXI design principles
axi-axi principles list
axi-axi principles show token-output

# Validate any CLI tool against AXI 1.0 automated checks (V01-V12)
axi-axi validate "agy-axi"
axi-axi validate "firefox-axi" --dir ~/.gemini/antigravity
```
