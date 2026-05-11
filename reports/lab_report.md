# Day 08 Lab Report

## 1. Team / student

- Name: Tạ Bảo Ngọc
- Repo/commit: [ngocbaoo/phase2-track3-day8-langgraph-agent](https://github.com/ngocbaoo/phase2-track3-day8-langgraph-agent)
- Date: 11/05/2026

## 2. Architecture

Kiến trúc của hệ thống LangGraph được thiết kế với các thành phần chính sau:
- **Nodes**: 
  - `intake_node`: Tiếp nhận và chuẩn hóa yêu cầu của người dùng.
  - `classify_node`: Phân loại yêu cầu dựa trên từ khóa (sử dụng regex boundaries) thành các `Route`: `simple`, `tool`, `missing_info`, `risky`, `error`.
  - `evaluate_node`: Đánh giá kết quả từ tool để quyết định vòng lặp thử lại (retry loop).
  - `approval_node`: Trạm kiểm duyệt (Human-in-the-loop) cho các tác vụ nguy hiểm.
  - Các node hành động: `tool_node`, `ask_clarification_node`, `risky_action_node`, `retry_or_fallback_node`, `dead_letter_node`, `answer_node`.
- **Edges**: Đồ thị có luồng rẽ nhánh linh hoạt (conditional edges) tại các điểm: sau khi phân loại (`classify`), sau khi đánh giá kết quả (`evaluate`), sau bước kiểm duyệt (`approval`) và sau mỗi lần thử lại (`retry`).
- **State Fields & Reducers**: Quản lý thông tin qua cấu trúc `TypedDict` cho phép theo dõi lịch sử thông qua `Annotated[list, add]`.

## 3. State schema

Danh sách các trường quan trọng và hành vi cập nhật:

| Field | Reducer | Why |
|---|---|---|
| `messages` | append (`add`) | Lưu vết (audit) toàn bộ hội thoại và hành động. |
| `tool_results` | append (`add`) | Lưu kết quả từ nhiều lần gọi tool, hỗ trợ cho việc đánh giá retry loop. |
| `events` | append (`add`) | Lưu sự kiện (audit trail) ở mỗi node phục vụ debug và tracking. |
| `errors` | append (`add`) | Ghi nhận chi tiết các lỗi trong quá trình retry. |
| `route` | overwrite | Chỉ lưu route hiện tại của query để quyết định rẽ nhánh. |
| `attempt` | overwrite | Lưu lại bộ đếm số lần đã thử lại (để so sánh với `max_attempts`). |
| `evaluation_result`| overwrite | Đóng vai trò là "cổng" (gate) điều hướng cho vòng lặp thử lại. |

## 4. Scenario results

Bảng thống kê từ kết quả chạy tự động `outputs/metrics.json`:

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|:---:|:---:|:---:|
| S01_simple | simple | simple | ✅ True | 0 | 0 |
| S02_tool | tool | tool | ✅ True | 0 | 0 |
| S03_missing | missing_info | missing_info | ✅ True | 0 | 0 |
| S04_risky | risky | risky | ✅ True | 0 | 1 |
| S05_error | error | error | ✅ True | 2 | 0 |
| S06_delete | risky | risky | ✅ True | 0 | 1 |
| S07_dead_letter | error | error | ✅ True | 0 | 0 |

*(Lưu ý: Kịch bản S07_dead_letter có max_attempts=1, nên retry_count là 0 do ngắt sớm ngay lần thử đầu tiên và đi vào `dead_letter_node` một cách an toàn và chính xác định tuyến `error`)*

## 5. Failure analysis

Phân tích các kịch bản lỗi:

1. **Retry or tool failure:** Khi tool gặp lỗi timeout/fail (`S05_error`), `evaluate_node` bắt được tín hiệu lỗi và trả về `"needs_retry"`. Graph sẽ rẽ vào `retry_node` để tăng biến đếm `attempt`. Quá trình này lặp lại cho đến khi thành công hoặc `attempt` chạm mức `max_attempts` (mặc định là 3), đảm bảo hệ thống không bị crash hoặc kẹt ở vòng lặp vô tận.
2. **Risky action without approval:** Đối với các query chứa từ khóa nhạy cảm như "refund", "delete" (`S04_risky`, `S06_delete`), `classify_node` ưu tiên định tuyến thành `Route.RISKY`. Điều này bắt buộc luồng phải đi qua `risky_action_node` để chuẩn bị hành động và dừng lại ở `approval_node`. Action chỉ được tiếp tục đi vào `tool` nếu `approval_node` trả về `approved=True`, tránh việc hệ thống tự ý xóa dữ liệu/hoàn tiền khi chưa được cho phép.

## 6. Persistence / recovery evidence

- **Checkpointer:** Đã triển khai thành công `SqliteSaver` trong `persistence.py` bằng `sqlite3` và chế độ WAL (Write-Ahead Logging).
- **Thread ID & State History:** Khi hệ thống chạy lệnh `run-scenarios`, cấu hình truyền vào có dạng `config={"configurable": {"thread_id": state["thread_id"]}}`. Do đó, LangGraph đã tự động phân mảnh và ghi chép từng thread tách biệt vào database cục bộ `checkpoints.db` (với dung lượng >300KB).
- **Ý nghĩa:** Điều này làm bằng chứng rõ ràng cho việc hệ thống có thể khôi phục lại trạng thái (crash-resume) hoặc dùng tính năng "du hành thời gian" (Time Travel) nhờ vào dữ liệu checkpointer đã được lưu vững chắc.

## 7. Extension work

**Graph Diagram Export:** 
Tôi đã thực hiện thêm một tính năng Bonus là tích hợp một câu lệnh CLI mới (`--draw-graph`). Tính năng này gọi hàm trích xuất đồ thị LangGraph đã được thiết lập để tự động xuất toàn bộ luồng kiến trúc (Nodes và Edges) ra mã Markdown Mermaid và lưu vào file `outputs/graph_diagram.md`. Điều này giúp mọi kiến trúc rẽ nhánh trở nên trực quan và có thể quan sát dễ dàng trên các trình biên dịch Markdown của GitHub hay IDE.

## 8. Improvement plan

Nếu được triển khai trên môi trường Production thực tế, tôi sẽ ưu tiên cải thiện các điểm sau:
1. **Nâng cấp Phân loại bằng AI (LLM):** Hệ thống heuristic (sử dụng regex & keyword cứng) ở `classify_node` hiện tại không hiểu được ngữ cảnh. Việc ứng dụng LLM Classifier hoặc prompt classifier sẽ giúp hiểu ý định mập mờ từ user.
2. **Cải tiến Evaluate Node (LLM-as-a-judge):** Đánh giá chất lượng của tool result bằng LLM (ví dụ kiểm tra xem JSON trả về có đúng format hay thiếu trường nào không) thay vì rà soát cứng chuỗi "ERROR".
3. **Phê duyệt trên giao diện (Streamlit UI):** Tích hợp UI frontend để chặn luồng thực sự (sử dụng tham số `LANGGRAPH_INTERRUPT=true` đã viết), từ đó cho phép Agent Admin có thể đọc "proposed_action" và chọn nút Phê duyệt / Từ chối trên màn hình trực quan.
