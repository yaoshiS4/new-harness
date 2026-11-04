# Performance Budget Guideline

**Trigger**: Task involves UI rendering, API endpoints, database queries, data processing, or LLM/agent orchestration.

## Core Web Vitals & Runtime Budgets
- **Largest Contentful Paint (LCP)**: $< 2.5\text{s}$ (target $< 1.8\text{s}$ on 4G/mid-tier mobile)
- **Interaction to Next Paint (INP)**: $< 200\text{ms}$ (target $< 100\text{ms}$ for primary interactive controls)
- **Cumulative Layout Shift (CLS)**: $< 0.10$ (zero layout shift from un-sized fonts/images or dynamic banners)
- **Animation & Scroll Frame Budget**: $60\text{fps}$ ($16.67\text{ms}$ per frame) / $120\text{fps}$ ProMotion ($8.33\text{ms}$); animate only compositor properties (`transform`, `opacity`)
- **Bundle Size**: $< 50\text{KB}$ gzipped per new route/chunk; zero unapproved heavy dependencies
- **Database & API Latency**: $< 50\text{ms}$ p95 for indexed single-record queries; $< 200\text{ms}$ p95 for standard API reads; zero N+1 query loops

## Cognitive & Agent Token Budgets
- **Path 1 (Quick Route)**: $\le 8,000$ context tokens, $\le 10$ tool calls
- **Path 2 (Normal Route)**: $\le 25,000$ context tokens, $\le 30$ tool calls
- **Path 3 (Long-Horizon Route)**: $\le 60,000$ context tokens, mandatory checkpoint at $60\%$ budget (`handoff_checkpoint` / `distill_observation_buffer`)
- **Global Rule Budget**: `antigravity/GLOBAL_AGENTS.md` strictly $\le 12,000$ characters (`validate-harness-tree.py`)

## Enforcement
- Profile before optimizing; measure baselines with concrete benchmarks rather than guessing.
- Declare explicit latency and token budgets in the Story Shard / task contract and verify before completion.
