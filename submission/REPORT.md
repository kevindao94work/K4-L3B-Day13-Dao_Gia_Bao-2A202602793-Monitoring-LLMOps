# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** ĐÀO GIA BẢO
- **MSSV:** 2A202602793
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/kevindao94work/K4-L3B-Day13-Dao_Gia_Bao-2A202602793-Monitoring-LLMOps
- **Commit SHA cuối:** `555f430` (commit chứa source và evidence; report cập nhật ngay sau đó)
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (K4, do Lab Coach cấp).
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602793` (đã xác minh qua API).

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata and usage | `evidence/08-trace-metadata-01.png`; cost chart in `evidence/08-trace-metadata-02.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt promote and rollback | `evidence/10a-prompt-promote.png`; `evidence/10b-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Không chạy được: chưa có `data/logs.jsonl`. | 100/100 trên 77 bản ghi tại thời điểm chụp. | Không có trường bắt buộc/enrichment thiếu, 36 correlation ID, không phát hiện PII. |
| `validate_dashboard.py` | 6/6 panel. | 6/6 panel. | Contract cấu hình hợp lệ. |
| `pytest` | Không thu được: thiếu `structlog` và `langfuse` khi chạy ngoài môi trường ảo. | 26 passed, 1 cảnh báo deprecation. | Chạy trong `.venv` theo `requirements.txt`. |
| Số traces hợp lệ | 0 xác minh được. | 36 root trace trong 24 giờ gần nhất; ảnh danh sách có 20 trace trong cửa sổ một giờ. | Đã xác minh qua Langfuse; ảnh UI ở evidence 06. |
| Số PII leak | Không có log để kiểm tra. | 0. | Kiểm tra validator và tìm bốn mẫu giả trong log đã ghi. |
| Latency P95 / TTFT P95 | Chưa có baseline CP0; lần chạy ổn định trước challenge có P95 161 ms. | 3 164 ms / 55 ms trong dashboard 60 phút. | Ảnh 12 ghi nhận 18 phản hồi; P95 vượt SLO 3 000 ms và ngưỡng challenge 2 000 ms. Batch challenge 5 request cũng có P95 3 164 ms. |
| Retrieval success rate | Chưa có baseline CP0. | 100%. | Dashboard ghi 18/18 tool events thành công; 5/5 request challenge có `tool_success=true`. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware giữ `x-request-id` hợp lệ theo mẫu `req-` kèm 8 ký tự hex viết thường; nếu thiếu hoặc không hợp lệ thì sinh mã mới. Mã được bind vào context, trả lại ở response header và ghi cùng request/response.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`, `correlation_id`, latency, TTFT, token, cost, quality và trạng thái retrieval.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy trước `JsonlFileProcessor` và JSON renderer; processor đệ quy qua các trường chuỗi và payload.
- **Cách kiểm chứng kết quả:** Request tạo cặp `request_received`/`response_sent` cùng correlation ID. Sáu log mẫu có marker email, điện thoại Việt Nam và thẻ thanh toán; validator phát hiện 0 rò rỉ. Output đã lọc nằm trong `evidence/05-redacted-log-samples.txt`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** SDK xác thực thành công; Langfuse hiển thị project `day13-k4-l3b-2A202602793`, với 36 root trace trong 24 giờ gần nhất.
- **Cấu trúc root/retrieval/generation observations:** Root trace chứa observation `lab-agent-run` với hai child `retrieval` và `generation`; cây nhìn thấy trong evidence 07.
- **Cách nối trace với log:** `correlation_id` nằm trong log và metadata observation. Ví dụ `req-1b8421d1` nối log challenge với trace `b9151c506c2109004331ef9876dc79c9`.
- **Prompt name:** `day13-chat`, managed prompt trên Langfuse.
- **Version/label baseline:** v1, label `baseline`; trace `6ce8ca3e07f1314825317f4d0f018637`.
- **Version/label candidate:** v2, label `candidate`; trace `d551a89a9a4162c6ed065e83dcb9cb3e`.
- **Trace ID của mỗi version:** v1 `6ce8ca3e07f1314825317f4d0f018637`; v2 `d551a89a9a4162c6ed065e83dcb9cb3e`; sau promote v2 `013c8c398ca675022c96e55966b1cfaf`; sau rollback v1 `112bfcf3b4c5d3fe21f7eb22f6df5e42`.
- **Cách promote và rollback `production`:** Đã chuyển `production` sang v2 và xác nhận trace dùng v2; sau đó đưa `production` về v1, giữ `candidate` ở v2 và xác nhận request mới dùng v1.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard cục bộ tại `/dashboard` đọc `data/logs.jsonl`, tự làm mới 30 giây và hiển thị latency/TTFT, traffic, error/retrieval, cost, token và quality; endpoint trả HTTP 200 với sáu panel, validator đạt 6/6. Ảnh 11–12 ghi lại overview và cửa sổ incident.
- **SLO và lý do chọn:** 99,5% request phải thành công trong 3.000 ms trên cửa sổ 28 ngày; ngưỡng này khớp contract của panel latency và mục tiêu lab.
- **Cách tính error budget:** 0,5% phần không đạt; với quy mô tham chiếu 10.000 request tương đương tối đa 50 request (`config/slo.yaml`).
- **Ba alert và runbook tương ứng:** `HighLatencyP95`, `ElevatedErrorRate`, `RetrievalOrQualityDegradation`; mỗi alert có severity, duration, owner, kênh Slack và runbook tại `docs/alerts.md`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (K4, file Lab Coach cấp).
- **Khoảng thời gian điều tra:** Baseline trước sự cố: 10 phản hồi, P95 161 ms. Workload challenge: 5 phản hồi từ `2026-09-30T05:35:10.241936Z` đến `2026-09-30T05:35:24.069415Z` UTC; P95 3 164 ms, vượt ngưỡng challenge 2 000 ms. Dashboard incident trong cửa sổ 60 phút ghi 18 phản hồi và P95 3 164 ms.
- **Triệu chứng từ metrics:** `response_sent.latency_ms` P95 tăng từ 161 ms lên 3 164 ms trong workload challenge; các request hoàn tất thành công.
- **Log line và correlation ID liên quan:** `response_sent` lúc `2026-09-30T05:35:21.402648Z`, `correlation_id=req-1b8421d1`, `session_id=k4-l3b-challenge-s04`, `latency_ms=2656`, `ttft_ms=50`, `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** Trace `b9151c506c2109004331ef9876dc79c9`; span `retrieval` kéo dài khoảng 2 503 ms, còn `generation` khoảng 153 ms.
- **Root cause:** Scenario challenge `rag_slow` chèn độ trễ vào retrieval; trace của cùng correlation ID cho thấy retrieval chiếm gần như toàn bộ thời gian request.
- **Fix action:** Tắt `rag_slow`; kiểm tra trạng thái incident đều false sau replay.
- **Preventive measure:** Giữ alert P95 latency và runbook Metrics → Logs → Traces; dùng correlation ID để kiểm tra retrieval trước khi thay đổi model hoặc prompt.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Dùng middleware contextvars cho correlation ID để giữ một mã xuyên suốt log và response; xóa context ở đầu/cuối request để tránh rò giữa request.
- **Một lỗi/blocker đã gặp:** Lần chạy đầu thiếu dependencies và base URL Langfuse không đúng region.
- **Cách tìm nguyên nhân và xử lý:** Tạo `.venv` Python 3.12, cài `requirements.txt`; sau khi cập nhật base URL, `auth_check` thành công và `/health` báo tracing hoạt động. Sau đó project được đổi tên theo yêu cầu và xác nhận qua API.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics xác định P95 challenge vượt ngưỡng; log chọn `req-1b8421d1`; trace cùng ID chỉ ra retrieval khoảng 2 503 ms gây chậm.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Version giúp truy vết prompt theo request; token/cost cho biết mức tiêu thụ; SLO định nghĩa mức dịch vụ và error budget; rollback khôi phục version ổn định khi có bằng chứng regression.
- **Điều quan trọng nhất đã học:** Redaction phải chạy trước khi log được serialize/ghi file; mã tương quan giúp nối log với trace mà không cần ghi raw user ID.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** CP0 chưa được ghi trước khi sửa; do đó baseline CP0 không có số liệu trực tiếp. Challenge evidence và UI screenshots đã được thu thập sau khi hoàn thiện ứng dụng.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence được đưa vào commit cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác trong các file được commit.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
