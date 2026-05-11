# Day 08 Lab Report

## Metrics summary

- Total scenarios: 7
- Success rate: 100.00%
- Average nodes visited: 19.29
- Total retries: 9
- Total interrupts: 6

## Architecture & State Schema

- **State Schema:** Dựa trên `TypedDict`, cấu trúc State được thiết kế bao gồm các trường trạng thái đơn (`route`, `risk_level`, `attempt`) và các trường lưu trữ lịch sử được thiết lập reducer `Annotated[list, add]` (như `messages`, `tool_results`, `errors`, `events`). Trường `evaluation_result` đóng vai trò là "cổng" (gate) cho vòng lặp thử lại sau khi gọi tool.
- **Graph Architecture:**
  - Bắt đầu với `intake` -> `classify` để phân loại query theo các từ khóa ưu tiên (như `risky`, `tool`, `missing_info`, `error`).
  - Graph rẽ nhánh nhờ conditional edges: 
    - Nhánh `risky` đi qua bước `approval`.
    - Nhánh `tool` đi vào `evaluate`. Nếu lỗi, tự động chuyển về `retry` tạo thành vòng lặp.
  - Mọi đường đi đều dẫn tới điểm tụ `finalize` trước khi kết thúc (END).

## Failure Modes & Retry Loop

- **Mô phỏng lỗi:** Với các truy vấn được phân vào Route `ERROR`, hệ thống giả lập "transient failure".
- **Giới hạn lặp:** Số lần gọi lại (retry) bị giới hạn bởi `max_attempts`. 
- **Dead letter:** Khi `attempt >= max_attempts`, logic điều hướng sẽ bắt ngoại lệ an toàn và chuyển vào `dead_letter` thay vì treo vô hạn (vượt qua kịch bản S07 thành công).

## Bonus Extension: Graph Diagram Export

Đã hoàn thiện tính năng Bonus **Graph Diagram Export**. Tôi bổ sung lệnh `--draw-graph` vào file `cli.py` để trích xuất sơ đồ cấu trúc của LangGraph thành mã Mermaid Markdown tự động, kết quả được lưu tại `outputs/graph_diagram.md`.

## Improvement Plan

- **Thay thế Heuristic bằng LLM**: Nâng cấp logic `classify_node` bằng một bộ phân loại LLM (vd: OpenAI/Gemini) hoặc LLM-as-a-judge trong `evaluate_node` thay vì so khớp từ khóa cứng.
- **Tích hợp UI**: Bổ sung Streamlit UI để quy trình phê duyệt HITL (Human-in-the-loop) trực quan và thân thiện với người thao tác hơn.
