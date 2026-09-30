# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`; duy trì 5 phút khi P95 latency vượt 3.000 ms. Kênh: Slack `#k4-l3b-alerts`.
- Metrics: xác nhận P95/P99, TTFT và thời điểm bắt đầu vượt ngưỡng trên cửa sổ 60 phút.
- Logs: lọc `response_sent` trong khoảng đó, sắp theo `latency_ms` giảm dần và chọn một `correlation_id` đại diện.
- Traces: mở trace cùng `correlation_id`, so thời lượng retrieval và generation để tìm span kéo dài.
- Mitigation: nếu trace xác nhận regression của prompt, chuyển `production` về version ổn định; nếu chưa rõ, giảm tải demo và tiếp tục theo dõi P95.
- Owner: `student-2A202602793`.

## Alert 2

- Tên: `ElevatedErrorRate`
- Severity: `critical`; error rate trên 2% liên tục 5 phút. Kênh: Slack `#k4-l3b-alerts`.
- Metrics: xác nhận error rate và thời điểm tăng; đối chiếu traffic để biết số request bị ảnh hưởng.
- Logs: lọc `request_failed` trong khoảng đó, nhóm theo `error_type` và lấy `correlation_id` đại diện.
- Traces: mở trace cùng `correlation_id`, kiểm tra trạng thái và lỗi ở retrieval/generation.
- Mitigation: khôi phục thành phần/config vừa đổi nếu trace hỗ trợ kết luận đó; tắt practice incident nếu đang bật, rồi theo dõi error rate.
- Owner: `student-2A202602793`.

## Alert 3

- Tên: `RetrievalOrQualityDegradation`
- Severity: `warning`; retrieval success dưới 90% hoặc quality proxy trung bình dưới 0,75 liên tục 10 phút. Kênh: Slack `#k4-l3b-alerts`.
- Metrics: xác nhận retrieval success, quality proxy và khoảng thời gian giảm.
- Logs: kiểm tra `tool_success`, `quality_score` và `correlation_id` của các request trong khoảng đó.
- Traces: mở trace cùng `correlation_id`, kiểm tra retrieval result và metadata prompt/version.
- Mitigation: khôi phục corpus hoặc prompt về trạng thái ổn định khi trace xác nhận liên quan; chạy lại workload mẫu để kiểm tra proxy phục hồi.
- Owner: `student-2A202602793`.
