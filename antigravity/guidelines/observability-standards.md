# Observability Standards Guideline

**Trigger**: Task adds or modifies services, API endpoints, MCP servers, workers, or background processes.

## Core Telemetry Pillar Requirements
- **Structured JSON Logging**:
  - Emit single-line JSON logs with mandatory fields: `timestamp` (ISO-8601 UTC), `level` (`DEBUG|INFO|WARN|ERROR`), `service`, `correlation_id` / `trace_id`, `operation`, `duration_ms`, and `status`.
  - Redact PII, tokens, cookies, and secret headers prior to serialization.
- **OpenTelemetry (OTel) Distributed Tracing**:
  - Propagate W3C `traceparent` headers across HTTP, RPC, and queue boundaries.
  - Instrument critical spans (DB queries, external API calls, subagent dispatches) with semantic attributes (`http.status_code`, `db.system`, `error.type`).
- **RED & USE Metrics**:
  - Track **R**ate (requests/sec), **E**rrors (error count by class), and **D**uration (p50, p95, p99 latency histograms) on all endpoints.
  - Monitor resource saturation (CPU, RSS memory, queue depth, SQLite WAL lock contention).
- **SLOs & Burn-Rate Alerting**:
  - Trigger fast-burn alerts when 5xx/error rate exceeds `1.0%`, p99 latency breaches the service budget, or Agent RSI severity burn rate $BR(W_{\text{short}}) \ge 3.0$ (`burn-rate-sentinel.py`).

## Implementation Checklist
- [ ] Log at `INFO` for state transitions/requests, `DEBUG` for diagnostic payloads, `ERROR` with structured stack traces for failures.
- [ ] Ensure every background job and subagent invocation carries a traceable `correlation_id`.
- [ ] Verify health/readiness probes (`/healthz`, `get_session_health`) return deterministic status codes.
