# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an educational lab template for teaching Monitoring, Logging, and Observability patterns in AI systems. It is a **gapped template** — students fill in missing implementations marked with `# TODO` comments throughout the codebase.

## Setup & Commands

```bash
# Environment setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure APP_ENV, LOG_LEVEL, LANGFUSE_* keys

# Run the application
uvicorn app.main:app --reload

# Testing
pytest
pytest tests/test_pii.py          # single test file
pytest tests/test_metrics.py -v   # verbose

# Lab scripts
python scripts/load_test.py --concurrency 5          # generate traffic
python scripts/inject_incident.py --scenario rag_slow  # inject failures
python scripts/validate_logs.py                        # validate log schema
```

## Architecture

**Request flow** for `POST /chat`:
1. `CorrelationIdMiddleware` (`app/middleware.py`) extracts or generates `x-request-id`, binds it to structlog context vars
2. Route handler (`app/main.py`) binds additional context: `user_id_hash`, `session_id`, `feature`, `model`, `env`
3. `LabAgent.run()` (`app/agent.py`) orchestrates:
   - `mock_rag.py` — simulated retrieval (injectable latency via incidents)
   - `mock_llm.py` — simulated LLM generation (injectable cost spikes)
   - Langfuse tracing via `@observe()` decorator
4. Structured JSON logs emitted via structlog → `data/logs.jsonl`
5. PII scrubbing applied in the logging pipeline (`app/pii.py` → `app/logging_config.py`)
6. In-memory metrics updated (`app/metrics.py`) — accessible at `GET /metrics`

**Key gapped files students must implement:**
- `app/middleware.py` — correlation ID propagation (clear contextvars, extract/generate ID, bind to structlog, set response header)
- `app/main.py` — bind user/session/feature/model to log context via `bind_contextvars()`
- `app/logging_config.py` — uncomment `scrub_event` processor in the structlog pipeline
- `app/pii.py` — extend PII regex patterns (passport numbers, address keywords, etc.)

## Configuration

| File | Purpose |
|------|---------|
| `config/logging_schema.json` | JSON Schema that `validate_logs.py` enforces on `data/logs.jsonl` |
| `config/slo.yaml` | SLI targets: `latency_p95`, `error_rate`, `daily_cost`, `quality_score` (28-day window) |
| `config/alert_rules.yaml` | P1/P2 alert rules: `high_latency_p95`, `high_error_rate`, `cost_budget_spike` |
| `config/incidents.json` | Named failure scenarios injectable via `/incidents/{name}/enable` |
| `.env.example` | All required environment variables — copy to `.env` before running |

## Observability Stack

- **Structured logging**: `structlog` with context vars; output format is JSONL at `data/logs.jsonl`
- **Tracing**: Langfuse SDK (`@observe()` decorator on agent methods); falls back gracefully if keys not set
- **Metrics**: In-memory aggregation in `app/metrics.py`; latency percentiles computed manually (no external library)
- **PII scrubbing**: Regex-based redaction in `app/pii.py`; applied as a structlog processor

## Lab Evaluation

Student submissions are graded against `docs/rubric.md`. The log schema in `config/logging_schema.json` is the authoritative contract — `validate_logs.py` exits non-zero if any log line fails schema validation.
