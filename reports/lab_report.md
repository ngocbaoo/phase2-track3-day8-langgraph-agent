# Day 08 Lab Report

## 1. Team / student

- Name: ngocbaoo
- Repo/commit: ngocbaoo/phase2-track3-day8-langgraph-agent
- Date: 11/05/2026

## 2. Architecture

Kiến trúc của hệ thống LangGraph được thiết kế với các thành phần chính sau:
- **Nodes**: 
  - `intake_node`: Tiếp nhận và chuẩn hóa yêu cầu.
  - `classify_node`: Phân loại yêu cầu dựa trên từ khóa thành các `Route`.
  - `evaluate_node`: Đánh giá kết quả từ tool để quyết định vòng lặp thử lại (retry loop).
  - `approval_node`: Trạm kiểm duyệt (Human-in-the-loop) cho các tác vụ nguy hiểm.
  - Các node hành động: `tool_node`, `ask_clarification_node`, `risky_action_node`, `retry_or_fallback_node`, `dead_letter_node`, `answer_node`.
- **Edges**: Đồ thị có luồng rẽ nhánh linh hoạt tại `classify`, `evaluate`, `approval` và `retry`.
- **State Fields & Reducers**: Quản lý thông tin qua cấu trúc `TypedDict`, theo dõi lịch sử qua `Annotated[list, add]`.

## 3. State schema

| Field | Reducer | Why |
|---|---|---|
| `messages` | append (`add`) | Lưu vết toàn bộ hội thoại và hành động. |
| `tool_results` | append (`add`) | Lưu kết quả từ nhiều lần gọi tool (để evaluate). |
| `events` | append (`add`) | Lưu sự kiện (audit trail) phục vụ debug. |
| `errors` | append (`add`) | Ghi nhận chi tiết các lỗi trong quá trình retry. |
| `route` | overwrite | Lưu route hiện tại của query để quyết định rẽ nhánh. |
| `attempt` | overwrite | Đếm số lần đã thử lại (để so sánh với `max_attempts`). |
| `evaluation_result`| overwrite | Đóng vai trò cổng (gate) điều hướng thử lại. |

## 4. Scenario results

- Total scenarios: 7
- Success rate: 100.00%
- Average nodes visited: 39.00
- Total retries: 18
- Total interrupts: 12

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|:---:|:---:|:---:|
| S01_simple | simple | simple | ✅ True | 0 | 0 |
| S02_tool | tool | tool | ✅ True | 0 | 0 |
| S03_missing | missing_info | missing_info | ✅ True | 0 | 0 |
| S04_risky | risky | risky | ✅ True | 0 | 1 |
| S05_error | error | error | ✅ True | 2 | 0 |
| S06_delete | risky | risky | ✅ True | 0 | 1 |
| S07_dead_letter | error | error | ✅ True | 0 | 0 |

## 5. Failure analysis

1. **Retry or tool failure:** Khi tool gặp lỗi (`S05_error`), `evaluate_node` bắt được và trả về `"needs_retry"`. Graph rẽ vào `retry_node` tăng `attempt` cho đến khi bằng `max_attempts` (giới hạn vô tận).
2. **Risky action without approval:** Query chứa "refund", "delete" ưu tiên vào `Route.RISKY`, bắt buộc dừng ở `approval_node`. Action chỉ tiếp tục khi `approved=True`.

## 6. Persistence / recovery evidence

- **Checkpointer:** Đã triển khai `SqliteSaver` trong `persistence.py` bằng `sqlite3` và WAL.
- **Bằng chứng:** Database `checkpoints.db` lưu từng thread tách biệt. Script `bonus_time_travel.py` minh chứng Crash Recovery (khôi phục sau sự cố ngắt kết nối) và Time Travel (tua lại các trạng thái cũ).

## 7. Extension work

Tôi đã thực hiện TOÀN BỘ các Bonus:
1. **Parallel fan-out:** Sử dụng `Send` để gọi 2 công cụ song song trong nhánh `TOOL`.
2. **Real HITL & Streamlit UI:** Tạo `app.py` giao diện chat tương tác có duyệt thủ công.
3. **Time travel & Crash recovery:** Tạo script `bonus_time_travel.py`.
4. **Graph Diagram Export:** Lệnh CLI `--draw-graph` sinh ra mã Mermaid.

## 8. Improvement plan

1. Nâng cấp bộ định tuyến `classify_node` bằng mô hình LLM thay vì Heuristic.
2. Nâng cấp `evaluate_node` bằng phương pháp LLM-as-a-judge.
