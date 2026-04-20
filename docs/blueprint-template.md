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
- [TRACE_WATERFALL_EXPLANATION]: Trace `LabAgent.run` có 1 generation span với model `claude-sonnet-4-5`, latency 0.15s, cost $0.00279, 210 tokens (30 input + 180 output). Metadata gồm `doc_count=1`, `query_preview` đã scrub PII, `user_id` đã hash SHA-256. Khi inject incident `rag_slow`, toàn bộ latency tập trung ở bước RAG retrieval (~2.5s), LLM chỉ chiếm ~150ms — trace waterfall chứng minh bottleneck nằm ở retrieval layer.

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
- [SYMPTOMS_OBSERVED]: Sau khi gọi `POST /incidents/rag_slow/enable`, latency P95 tăng từ ~155ms lên 2664–7989ms. Các log dòng `response_sent` liên tục có `latency_ms > 2500`. Metrics endpoint báo `latency_p95 = 2659ms`, vượt SLO objective 3000ms trong điều kiện concurrency cao.
- [ROOT_CAUSE_PROVED_BY]: Trace waterfall Langfuse (trace id `8954cbd4e5440a910dff601c0328f33b`) cho thấy span `LabAgent.run` mất 2.664s — toàn bộ thời gian nằm ở retrieval, không phải LLM. Log line: `{"event": "response_sent", "latency_ms": 2664, "correlation_id": "req-82d07d65", "feature": "qa", "session_id": "s08"}`. Nguồn gốc: `mock_rag.py` dòng 13 — `time.sleep(2.5)` khi `STATE["rag_slow"] is True`.
- [FIX_ACTION]: Gọi `POST /incidents/rag_slow/disable` — latency hồi phục về <200ms ngay lập tức, không cần restart service.
- [PREVENTIVE_MEASURE]: (1) Thêm alert `rag_slow_detected`: `rag_span_p95_ms > 1000 for 5m`, severity P2 — phát hiện sớm trước khi SLO breach (đã thêm vào `config/alert_rules.yaml`). (2) Đặt timeout 1s cho RAG retrieval với fallback answer khi vượt quá. (3) Circuit breaker: tự động bypass RAG sau 3 lần timeout liên tiếp trong 1 phút.

---

## 5. Individual Contributions & Evidence

### Nguyen Huu Tan Long (2A202600168) — Role A: Logging & PII

- [TASKS_COMPLETED]:
  - Implement `app/middleware.py` — `CorrelationIdMiddleware`: gọi `clear_contextvars()` đầu mỗi request để tránh context leak giữa các request; extract header `x-request-id` nếu có hoặc generate `req-<uuid_hex[:8]>`; bind `correlation_id` vào structlog context; gắn `x-request-id` và `x-response-time-ms` vào response header.
  - Implement `app/main.py` — tại endpoint `/chat`: gọi `bind_contextvars(user_id_hash=hash_user_id(...), session_id=..., feature=..., model=..., env=...)` để mọi log trong request đều có đủ context. Thêm `load_dotenv()` để load biến môi trường từ `.env`.
  - Implement `app/logging_config.py` — bật `scrub_event` processor trong pipeline structlog, đặt sau `TimeStamper` để PII trong `payload` và `event` được redact trước khi ghi file.
  - Implement `app/pii.py` — thêm pattern `passport` (`\b[A-Z]\d{7,8}\b`) cho số hộ chiếu Việt Nam; thêm `address_vn` cho các từ khóa địa chỉ (số, đường, phường, quận, tỉnh, thành phố, huyện, xã); đặt `cccd` trước `phone_vn` trong dict để tránh phone pattern match nhầm 12 chữ số CCCD.
  - Viết 5 test cases mới trong `tests/test_pii.py`: `test_scrub_phone_vn`, `test_scrub_cccd`, `test_scrub_passport`, `test_scrub_credit_card`, `test_no_false_positive`. Tất cả 11/11 tests pass.
- [EVIDENCE_LINK]: https://github.com/Tan-Long/_lab13_/commit/8e9a84f — files: `app/middleware.py`, `app/main.py`, `app/logging_config.py`, `app/pii.py`, `tests/test_pii.py`

---

### Nguyen Huu Tan Long (2A202600168) — Role B: Tracing & Enrichment

- [TASKS_COMPLETED]:
  - Phát hiện `langfuse.decorators` không tồn tại ở Langfuse v3 — rewrite `app/tracing.py` dùng `from langfuse import observe, get_client` theo v3 API. Implement `flush_traces()` gọi `_langfuse_client.flush()` sau mỗi request để đảm bảo traces được đẩy lên server ngay, không bị mất khi worker bị recycle.
  - Cập nhật `app/agent.py` — đổi `update_current_observation()` (v2, không còn tồn tại) sang `update_current_generation()` (v3); truyền `model=self.model` để Langfuse nhận diện model name; thêm `usage_details` (input/output/total tokens) và `cost_details` (input_cost/output_cost/total_cost USD) để dashboard hiển thị đúng cost và usage.
  - Kết quả: 43 traces trên Langfuse với đầy đủ latency, cost ($0.0806 tổng), tokens (1387 in / 5095 out), user_id_hash, session_id, tags `["lab", feature, model]`.
- [EVIDENCE_LINK]: https://github.com/Tan-Long/_lab13_/commit/8e9a84f — files: `app/tracing.py`, `app/agent.py`; ảnh: `docs/evidence/trace_waterfall.png`

---

### Nguyen Huu Tan Long (2A202600168) — Role C: SLO & Alerts

- [TASKS_COMPLETED]:
  - Cập nhật `config/slo.yaml` — thêm `measured` và `status` thực tế cho 4 SLIs dựa trên kết quả chạy thực: latency P95=155ms (PASSING vs target 3000ms), error_rate=0% (PASSING), cost=$0.002/req (PASSING vs $2.5/day), quality=0.88 (PASSING vs 0.75).
  - Mở rộng `config/alert_rules.yaml` từ 3 lên 5 alert rules:
    - `high_latency_p95` (P2): tighten threshold từ 5000ms → 3000ms để align với SLO, thêm `notify: slack#oncall-alerts`.
    - `high_error_rate` (P1): thêm `notify: pagerduty` cho P1 severity.
    - `cost_budget_spike` (P2): thêm `notify: slack#finops`.
    - `rag_slow_detected` (P2) — **alert mới**: `rag_span_p95_ms > 1000 for 5m` — early warning, bắt bottleneck RAG trước khi latency SLO breach. Được thêm dựa trên bài học từ incident `rag_slow`.
    - `quality_degradation` (P3) — **alert mới**: `quality_score_avg < 0.6 for 30m` — phát hiện model output quality giảm.
  - Viết runbook đầy đủ cho 3 alerts chính tại `docs/alerts.md` với first checks và mitigation steps cụ thể.
- [EVIDENCE_LINK]: https://github.com/Tan-Long/_lab13_/commit/48a5943 — files: `config/slo.yaml`, `config/alert_rules.yaml`; ảnh: `docs/evidence/alert_rules.png`

---

### Nguyen Huu Tan Long (2A202600168) — Role D: Load Test & Incident Injection

- [TASKS_COMPLETED]:
  - Chạy `python scripts/load_test.py --concurrency 5` tổng cộng 5 lần — **50 requests** với 10 user/session khác nhau, feature `qa` và `summary` xen kẽ.
  - Inject incident `rag_slow`: `POST /incidents/rag_slow/enable` → gửi 10 requests concurrent → quan sát latency tăng lên 2664–7989ms → `POST /incidents/rag_slow/disable` → latency hồi phục. Ghi lại correlation IDs của slow requests để dùng làm evidence trong incident response.
  - Chạy `python scripts/validate_logs.py` sau mỗi batch — kết quả cuối: **207 log records, 102 unique correlation IDs, 0 missing required fields, 0 PII leaks, 100/100**.
  - Verify metrics endpoint: `traffic=50, latency_p50=153ms, latency_p95=155ms, error_breakdown={}, quality_avg=0.88, total_cost_usd=$0.0978`.
- [EVIDENCE_LINK]: `data/logs.jsonl` (207 records); ảnh: `docs/evidence/correlation_id.png`, `docs/evidence/metrics_snapshot.png`

---

### Nguyen Huu Tan Long (2A202600168) — Role E: Dashboard & Evidence

- [TASKS_COMPLETED]:
  - Xây dựng 6-panel dashboard từ Langfuse Maintained Dashboards và `/metrics` endpoint:
    1. **Latency P50/P95/P99** — `docs/evidence/latency_dashboard.png` (Langfuse Latency Dashboard)
    2. **Traffic** — `docs/evidence/cost_dashboard_2.png` (Total Count Traces = 33)
    3. **Error Rate** — `docs/evidence/metrics_snapshot.png` (`error_breakdown: {}`, error rate = 0%)
    4. **Cost over time** — `docs/evidence/cost_dashboard_2.png` (Total costs chart, $0.08 tổng)
    5. **Tokens in/out** — `docs/evidence/metrics_snapshot.png` (`tokens_in=1360, tokens_out=4965`)
    6. **Quality proxy** — `docs/evidence/metrics_snapshot.png` (`quality_avg=0.88`)
  - Thu thập 8 evidence screenshots: `correlation_id.png`, `pii_redaction.png`, `trace_waterfall.png`, `cost_dashboard_1.png`, `cost_dashboard_2.png`, `latency_dashboard.png`, `metrics_snapshot.png`, `alert_rules.png`.
  - Tổ chức evidence vào `docs/evidence/` và cập nhật đường dẫn trong báo cáo.
- [EVIDENCE_LINK]: `docs/evidence/` (8 files); `docs/evidence/cost_dashboard_2.png`, `docs/evidence/latency_dashboard.png`

---

### Nguyen Huu Tan Long (2A202600168) — Role F: Blueprint & Demo Lead

- [TASKS_COMPLETED]:
  - Viết và hoàn thiện toàn bộ báo cáo `docs/blueprint-template.md` — 6 sections, SLO table với measured values, incident response đầy đủ root cause + fix + preventive measure, individual contribution cho 6 roles.
  - Chuẩn bị demo script (5 phút):
    1. `curl http://localhost:8000/health` → confirm `tracing_enabled: true`
    2. `python scripts/load_test.py --concurrency 5` → show requests với correlation IDs
    3. `POST /incidents/rag_slow/enable` → show latency spike trên terminal
    4. Mở Langfuse → show trace waterfall với span breakdown
    5. `POST /incidents/rag_slow/disable` → show latency recovery
    6. `python scripts/validate_logs.py` → live 100/100
    7. Show `docs/evidence/` — tất cả 8 screenshots
  - Tạo `CLAUDE.md` với architecture overview, setup commands, và hướng dẫn cho repo.
- [EVIDENCE_LINK]: https://github.com/Tan-Long/_lab13_/commit/48a5943 — files: `docs/blueprint-template.md`, `CLAUDE.md`

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Thêm 2 alert rules mới (`rag_slow_detected` P2, `quality_degradation` P3) và tighten `high_latency_p95` từ 5000ms → 3000ms để align với SLO. Alert `rag_slow_detected` phát hiện bottleneck sớm trước khi SLO breach, giúp team response trước khi user bị ảnh hưởng diện rộng. Evidence: `config/alert_rules.yaml`, `docs/evidence/alert_rules.png`.
- [BONUS_AUDIT_LOGS]: `LOG_PATH` configurable qua `.env` (mặc định `data/logs.jsonl`). Có thể đổi sang `data/audit.jsonl` để tách audit log riêng. `JsonlFileProcessor` tự tạo thư mục parent nếu chưa tồn tại. Evidence: `app/logging_config.py`, `.env`.
- [BONUS_CUSTOM_METRIC]: `quality_avg` trong `GET /metrics` — heuristic score tính từ: doc retrieval hit (+0.2), answer length > 40 chars (+0.1), keyword overlap với question (+0.1), penalty nếu có `[REDACTED` trong answer (-0.2). Current value: 0.88/1.0. Thêm SLI `quality_score_avg ≥ 0.75` vào `config/slo.yaml` với status PASSING. Evidence: `app/metrics.py`, `app/agent.py`, `docs/evidence/metrics_snapshot.png`.
