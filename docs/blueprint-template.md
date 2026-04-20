# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Solo-2A202600168
- [REPO_URL]: https://github.com/Tan-Long/_lab13_
- [MEMBERS]:
  - Member A: Nguyen Huu Tan Long (2A202600168) | Role: Logging & PII
  - Member B: Nguyen Huu Tan Long (2A202600168) | Role: Tracing & Enrichment
  - Member C: Nguyen Huu Tan Long (2A202600168) | Role: SLO & Alerts
  - Member D: Nguyen Huu Tan Long (2A202600168) | Role: Load Test & Incident Injection
  - Member E: Nguyen Huu Tan Long (2A202600168) | Role: Dashboard & Evidence
  - Member F: Nguyen Huu Tan Long (2A202600168) | Role: Blueprint & Demo Lead

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 43
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/evidence/correlation_id.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/evidence/pii_redaction.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/evidence/trace_waterfall.png
- [TRACE_WATERFALL_EXPLANATION]: Trace `LabAgent.run` có 1 generation span với model `claude-sonnet-4-5`, latency 0.15s, cost $0.00279, 210 tokens (30 input + 180 output). Metadata gồm `doc_count`, `query_preview`, `user_id` đã hash. Khi inject `rag_slow`, latency tăng lên ~2.6–8s — trace waterfall cho thấy rõ bottleneck nằm ở bước retrieval trước khi LLM generate.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/evidence/cost_dashboard_2.png + docs/evidence/latency_dashboard.png + docs/evidence/metrics_snapshot.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value | Status |
|---|---:|---|---:|---|
| Latency P95 | < 3000ms | 28d | 155ms (normal) | PASSING |
| Error Rate | < 2% | 28d | 0% | PASSING |
| Cost Budget | < $2.5/day | 1d | $0.002/req avg | PASSING |
| Quality Score | > 0.75 | 28d | 0.88 | PASSING |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: docs/evidence/alert_rules.png
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md#1-high-latency-p95

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Latency P95 tăng đột biến từ ~155ms lên ~2664–7989ms sau khi gọi `POST /incidents/rag_slow/enable`. Log liên tục xuất hiện `latency_ms > 2500`. Metrics endpoint cho thấy `latency_p95` vượt SLO 3000ms.
- [ROOT_CAUSE_PROVED_BY]: (1) Trace waterfall Langfuse: span `LabAgent.run` chiếm 2.6s, toàn bộ do retrieval. (2) Log thực tế: `{"event": "response_sent", "latency_ms": 2664, "correlation_id": "req-82d07d65", "feature": "qa"}`. (3) Source code `mock_rag.py:13` — `time.sleep(2.5)` khi `STATE["rag_slow"] is True`.
- [FIX_ACTION]: `POST /incidents/rag_slow/disable` — latency trở về <200ms ngay lập tức.
- [PREVENTIVE_MEASURE]: (1) Thêm alert `rag_slow_detected` (đã có trong `config/alert_rules.yaml`): `rag_span_p95_ms > 1000 for 5m`, severity P2. (2) Timeout 1s cho RAG retrieval với fallback answer. (3) Circuit breaker: bypass RAG sau 3 lần timeout liên tiếp.

---

## 5. Individual Contributions & Evidence

### Nguyen Huu Tan Long (2A202600168) — Role A: Logging & PII

- [TASKS_COMPLETED]:
  - `app/middleware.py`: implement `CorrelationIdMiddleware` — `clear_contextvars()`, extract `x-request-id` từ header hoặc generate `req-<8hex>`, bind vào structlog, set response headers `x-request-id` và `x-response-time-ms`.
  - `app/main.py`: `bind_contextvars(user_id_hash, session_id, feature, model, env)` tại `/chat` endpoint; thêm `load_dotenv()` để load Langfuse keys.
  - `app/logging_config.py`: bật `scrub_event` processor trong structlog pipeline.
  - `app/pii.py`: thêm pattern `passport` (`\b[A-Z]\d{7,8}\b`) và `address_vn`; đặt `cccd` trước `phone_vn` để tránh partial match trên 12-digit strings.
  - `tests/test_pii.py`: thêm 5 test cases — phone_vn, cccd, passport, credit_card, no_false_positive.
- [EVIDENCE_LINK]: commit `8e9a84f` — files: `app/middleware.py`, `app/main.py`, `app/logging_config.py`, `app/pii.py`, `tests/test_pii.py`

---

### Nguyen Huu Tan Long (2A202600168) — Role B: Tracing & Enrichment

- [TASKS_COMPLETED]:
  - `app/tracing.py`: migrate từ `langfuse.decorators` (v2, không tồn tại ở v3) sang Langfuse v3 API — dùng `from langfuse import observe, get_client`; implement `flush_traces()` để đảm bảo traces được gửi sau mỗi request.
  - `app/agent.py`: thêm `cost_details` (input/output/total USD) và `usage_details` (input/output/total tokens) vào `update_current_generation()`; set `model=self.model` để Langfuse hiển thị đúng model name; tag trace với `["lab", feature, model]`.
  - Kết quả: **43 traces** gửi thành công lên Langfuse với cost, latency, tokens, user_id_hash, session_id, tags đầy đủ.
- [EVIDENCE_LINK]: commit `8e9a84f` — files: `app/tracing.py`, `app/agent.py`; evidence: `docs/evidence/trace_waterfall.png`

---

### Nguyen Huu Tan Long (2A202600168) — Role C: SLO & Alerts

- [TASKS_COMPLETED]:
  - `config/slo.yaml`: cập nhật 4 SLIs với `measured` và `status` thực tế — tất cả PASSING. Latency P95 155ms vs target 3000ms; error rate 0%; cost $0.002/req; quality 0.88.
  - `config/alert_rules.yaml`: mở rộng từ 3 lên **5 alert rules**:
    - `high_latency_p95` (P2): tightened condition từ 5000ms → 3000ms để match SLO
    - `high_error_rate` (P1): notify PagerDuty
    - `cost_budget_spike` (P2): notify Slack #finops
    - `rag_slow_detected` (P2): **mới** — early warning trước khi SLO breach
    - `quality_degradation` (P3): **mới** — phát hiện model quality giảm
  - Runbook đầy đủ tại `docs/alerts.md` cho cả 3 alert gốc.
- [EVIDENCE_LINK]: commit `7862a93` + staged — files: `config/slo.yaml`, `config/alert_rules.yaml`; evidence: `docs/evidence/alert_rules.png`

---

### Nguyen Huu Tan Long (2A202600168) — Role D: Load Test & Incident Injection

- [TASKS_COMPLETED]:
  - Chạy `python scripts/load_test.py --concurrency 5` nhiều lần — tổng **50 requests** tới `/chat` endpoint với user/session/feature đa dạng.
  - Inject và verify incident `rag_slow`: `POST /incidents/rag_slow/enable` → latency tăng 10–50x → `POST /incidents/rag_slow/disable` → latency về bình thường.
  - Kết quả load test thực tế: traffic=50, latency_p50=153ms, latency_p95=155ms, error_breakdown={} (0 errors), quality_avg=0.88.
  - Validate: `python scripts/validate_logs.py` → 187 log records, 92 unique correlation IDs, 0 PII leaks — **100/100**.
- [EVIDENCE_LINK]: `data/logs.jsonl` (187 records); evidence: `docs/evidence/correlation_id.png`, `docs/evidence/metrics_snapshot.png`

---

### Nguyen Huu Tan Long (2A202600168) — Role E: Dashboard & Evidence

- [TASKS_COMPLETED]:
  - Thu thập **8 evidence screenshots** từ Langfuse dashboard và terminal output:
    - `correlation_id.png` — log JSON với `req-xxxxxxxx` trên mọi dòng
    - `pii_redaction.png` — `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]` trong logs
    - `trace_waterfall.png` — Langfuse trace detail: latency 0.15s, $0.00279, 210 tokens
    - `cost_dashboard_1.png` + `cost_dashboard_2.png` — 33 traces, $0.08 total cost, top users by cost
    - `latency_dashboard.png` — P95 latency chart, max latency by user
    - `metrics_snapshot.png` — `/metrics` endpoint: traffic, latency P50/P95/P99, cost, tokens, quality
    - `alert_rules.png` — `config/alert_rules.yaml` với 5 alert rules
  - 6-panel dashboard coverage: Latency (✅), Traffic (✅), Error Rate (✅), Cost (✅), Tokens (✅), Quality (✅)
- [EVIDENCE_LINK]: `docs/evidence/` (8 files)

---

### Nguyen Huu Tan Long (2A202600168) — Role F: Blueprint & Demo Lead

- [TASKS_COMPLETED]:
  - Viết và hoàn thiện toàn bộ báo cáo `docs/blueprint-template.md` — điền đầy đủ 6 sections, SLO table, incident response, individual contributions cho cả 6 roles.
  - Chuẩn bị demo flow: app chạy tại `uvicorn app.main:app --port 8000`; demo sequence: (1) gọi `/health` confirm tracing enabled, (2) gửi requests qua load_test.py, (3) inject `rag_slow` → show latency spike trên Langfuse, (4) disable → show recovery, (5) `validate_logs.py` 100/100 live.
  - CLAUDE.md: tạo documentation hướng dẫn setup và architecture cho repo.
- [EVIDENCE_LINK]: `docs/blueprint-template.md`, `CLAUDE.md`

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: 5 alert rules thay vì 3 — thêm `rag_slow_detected` (P2) và `quality_degradation` (P3). `rag_slow_detected` bắt bottleneck sớm trước khi SLO breach, giúp giảm chi phí latency tail. Evidence: `config/alert_rules.yaml`.
- [BONUS_AUDIT_LOGS]: `LOG_PATH` configurable qua `.env` — có thể dùng `data/audit.jsonl` để ghi audit log riêng. `JsonlFileProcessor` tự tạo thư mục nếu chưa có.
- [BONUS_CUSTOM_METRIC]: `quality_avg=0.88` trong `GET /metrics` — heuristic score dựa trên doc retrieval hit, answer length, keyword overlap, và PII-free output. Thêm SLI `quality_score_avg` vào `config/slo.yaml` với target 0.75.
