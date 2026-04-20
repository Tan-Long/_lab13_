# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Solo-2A202600168
- [REPO_URL]: https://github.com/Tan-Long/_lab13_
- [MEMBERS]:
  - Member A: Nguyen Huu Tan Long (2A202600168) | Role: Logging & PII

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 33
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/evidence/correlation_id.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/evidence/pii_redaction.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/evidence/trace_waterfall.png
- [TRACE_WATERFALL_EXPLANATION]: Span `LabAgent.run` gồm 2 sub-spans: `mock_rag.retrieve` (~150ms bình thường, ~2650ms khi `rag_slow=True`) và `mock_llm.generate` (~150ms). Khi kích hoạt incident `rag_slow`, span retrieve chiếm hơn 90% tổng thời gian, chứng minh bottleneck nằm ở tầng RAG chứ không phải LLM.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/evidence/cost_dashboard_2.png + docs/evidence/latency_dashboard.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 2659ms (incl. rag_slow incident) / ~320ms (normal) |
| Error Rate | < 2% | 28d | 0% (0 errors / 30 requests) |
| Cost Budget | < $2.5/day | 1d | $0.0018/request avg, $0.0532 total (30 requests) |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: docs/evidence/alert_rules.png
- [METRICS_SNAPSHOT_SCREENSHOT]: docs/evidence/metrics_snapshot.png
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md#1-high-latency-p95

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Latency P95 tăng đột biến từ ~320ms lên ~2700ms sau khi gọi `POST /incidents/rag_slow/enable`. Log xuất hiện `latency_ms > 2500` liên tục. Dashboard panel "Latency P50/P95/P99" cho thấy P95 vượt ngưỡng SLO 3000ms.
- [ROOT_CAUSE_PROVED_BY]: Trace waterfall trong Langfuse cho thấy span `retrieve` trong `LabAgent.run` chiếm ~2500ms/~7980ms tổng latency. Log line thực tế: `{"event": "response_sent", "latency_ms": 2664, "correlation_id": "req-82d07d65", ...}`. Source code: `mock_rag.py:13` — `time.sleep(2.5)` khi `STATE["rag_slow"] is True`. Validate script xác nhận: 30 traces, 0 PII leaks, correlation ID đầy đủ.
- [FIX_ACTION]: Gọi `POST /incidents/rag_slow/disable` để tắt incident. Latency trở về bình thường (<400ms) ngay lập tức.
- [PREVENTIVE_MEASURE]: (1) Đặt timeout cho RAG retrieval (ví dụ 1s) và fallback sang general answer khi timeout. (2) Thêm alert `rag_latency_p95 > 1000ms for 5m` với severity P2 để phát hiện sớm. (3) Circuit breaker pattern: nếu RAG fail/slow liên tiếp 3 lần, tự động bypass RAG.

---

## 5. Individual Contributions & Evidence

### Nguyen Huu Tan Long (2A202600168)

- [TASKS_COMPLETED]:
  1. **Logging & PII (Member A role)**
     - Implement `app/middleware.py`: `CorrelationIdMiddleware` — clear contextvars, extract/generate `x-request-id` (format `req-<8hex>`), bind vào structlog, gắn headers `x-request-id` và `x-response-time-ms` vào response.
     - Implement `app/main.py`: bind `user_id_hash`, `session_id`, `feature`, `model`, `env` vào structlog context tại `/chat` endpoint.
     - Implement `app/logging_config.py`: bật `scrub_event` processor trong pipeline structlog để PII scrubbing tự động áp dụng cho tất cả log.
     - Implement `app/pii.py`: thêm pattern `passport` (VD: B1234567) và `address_vn` (số nhà, đường, phường, quận, tỉnh, thành phố, huyện, xã).
     - Viết thêm 9 test cases bổ sung trong `tests/test_pii.py` (phone, CCCD, passport, credit card, no-false-positive) và `tests/test_metrics.py` (empty list, p95, single value, snapshot structure). Tất cả **11/11 tests pass**.

- [EVIDENCE_LINK]: Xem commit history — các file thay đổi: `app/middleware.py`, `app/main.py`, `app/logging_config.py`, `app/pii.py`, `tests/test_pii.py`, `tests/test_metrics.py`

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Khi inject `cost_spike`, `tokens_out` tăng 4x → cost tăng ~4x. Giải pháp: giới hạn `max_tokens` trong LLM call và log cảnh báo khi `cost_usd > threshold` mỗi request. Evidence: `GET /metrics` → `avg_cost_usd` so sánh trước/sau disable `cost_spike`.
- [BONUS_AUDIT_LOGS]: Cấu hình `LOG_PATH=data/audit.jsonl` qua `.env` để ghi audit log riêng biệt với application log. File `data/audit.jsonl` được tạo tự động bởi `JsonlFileProcessor`.
- [BONUS_CUSTOM_METRIC]: Thêm field `quality_avg` vào `GET /metrics` (đã có trong `app/metrics.py::snapshot()`). Quality score được tính bằng heuristic trong `agent.py::_heuristic_quality()` — kiểm tra độ dài answer, keyword overlap, và không có `[REDACTED` trong output.
