# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Nhóm 12
- **Team Members**:
  - 2A202600001 - Bùi Cao Chinh
  - 2A202600408 - Nguyễn Tiến Đạt
  - 2A202600432 - Trần Thị Kim Ngân
  - 2A202600393 - Nguyễn Đức Tiến
  - 2A202600227 - Nguyễn Trọng Thiên Khôi
  - 2A202600492 - Phan Xuân Quang Linh
  - 2A202600107 - Lê Thị Phương
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

Agent ReAct được kiểm thử trên **5 test case** cùng bộ câu hỏi với Chatbot Baseline, chạy trên model **gpt-4o** (OpenAI).

- **Success Rate**: Agent 80% (4/5) · Chatbot 60% (3/5)
- **Key Outcome**: Agent giải quyết đúng 100% các query multi-step (lọc theo nhiều tiêu chí + kiểm tra giờ mở cửa) nhờ chuỗi tool calls. Chatbot trả lời được câu hỏi đơn giản nhưng không có dữ liệu thực tế, dễ hallucinate tên/giá quán. Agent thua ở chi phí token — đắt hơn ~5.8x so với chatbot trên cùng bộ test.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

![Flowchart Diagram](/docs/images/flowchart-day3.png)

Vòng lặp ReAct trong `src/agent/agentV1.py`:

1. LLM sinh ra **Thought** → phân tích yêu cầu
2. LLM chọn **Action** + **Action Input** → parse bằng regex
3. **Tool** thực thi → trả về **Observation**
4. Lặp lại cho đến khi có **Final Answer** hoặc đạt `max_steps = 5`

### 2.2 Tool Definitions (Inventory)

| Tool Name                   | Input Format  | Use Case                                                                    |
| :-------------------------- | :------------ | :-------------------------------------------------------------------------- |
| `search_restaurants`        | `JSON/kwargs` | Tìm danh sách quán theo cuisine, district, price, rating, ambiance, amenity |
| `get_restaurant_details`    | `string`      | Lấy thông tin chi tiết (địa chỉ, giờ mở cửa, tiện ích) của một quán cụ thể  |
| `check_open_status`         | `JSON/kwargs` | Kiểm tra quán có đang mở cửa tại thời điểm HH:MM không                      |
| `calculate_estimated_cost`  | `JSON/kwargs` | Tính tổng chi phí ước tính cho N người tại một quán                         |
| `human_escalation_fallback` | `string`      | Chuyển yêu cầu sang hỗ trợ thủ công khi agent không xử lý được              |

### 2.3 LLM Providers Used

- **Primary**: GPT-4o (OpenAI)
- **Telemetry**: `src/telemetry/logger.py` (structured JSON log) + `src/telemetry/metrics.py` (token/latency/cost tracking)

---

## 3. Telemetry & Performance Dashboard

Số liệu lấy trực tiếp từ `logs/2026-04-06.log` — 5 query chatbot (dòng 1–15) và 5 query agent (dòng 16+).

### 3.1 Chatbot Baseline

| Query                                                |                    Latency (ms) | Total Tokens |   Cost ($) |
| :--------------------------------------------------- | ------------------------------: | -----------: | ---------: |
| "quán ăn ngon"                                       |                           4,751 |          302 |    0.00302 |
| "Nhà hàng Pháp Tây Hồ < 500k cho 2 người"            |                           1,872 |          480 |    0.00480 |
| "tìm quán chay tại Thanh Xuân"                       |                           3,030 |          670 |    0.00670 |
| "tìm sân bóng"                                       |                           2,071 |          813 |    0.00813 |
| "quán lãng mạn đồ nhật có chỗ để xe đang mở lúc 20h" |                           4,026 |        1,031 |    0.01031 |
| **Tổng / Trung bình**                                | **P50: 3,030ms · P99: 4,751ms** | **avg: 659** | **$0.033** |

### 3.2 ReAct Agent

| Query                                                |      Steps |                     Tool Calls |                    Latency (ms) |   Total Tokens |   Cost ($) |
| :--------------------------------------------------- | ---------: | -----------------------------: | ------------------------------: | -------------: | ---------: |
| "quán ăn ngon"                                       |          1 |                              0 |                           3,088 |          1,506 |    0.01506 |
| "Nhà hàng Pháp Tây Hồ < 500k cho 2 người"            |          2 |       1 (`search_restaurants`) |                           7,345 |          3,543 |    0.03543 |
| "tìm quán chay tại Thanh Xuân"                       |          2 |       1 (`search_restaurants`) |                           4,429 |          3,585 |    0.03585 |
| "tìm sân bóng"                                       |          1 |                              0 |                           1,968 |          1,789 |    0.01789 |
| "quán lãng mạn đồ nhật có chỗ để xe đang mở lúc 20h" |          4 | 3 (`search` + `check_open` ×2) |                           6,983 |          8,679 |    0.08679 |
| **Tổng / Trung bình**                                | **avg: 2** |                     **avg: 1** | **P50: 4,429ms · P99: 7,345ms** | **avg: 3,820** | **$0.171** |

### 3.3 So sánh tổng hợp

| Metric                 | Chatbot |   Agent |          Chênh lệch |
| :--------------------- | ------: | ------: | ------------------: |
| P50 Latency            | 3,030ms | 4,429ms | Agent chậm hơn 1.5x |
| P99 Latency            | 4,751ms | 7,345ms | Agent chậm hơn 1.5x |
| Avg Tokens/query       |     659 |   3,820 |  Agent tốn hơn 5.8x |
| Total Cost (5 queries) |  $0.033 |  $0.171 |  Agent đắt hơn 5.2x |

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Agent loop vô hạn khi query ngoài scope — "quán ăn Đà Nẵng"

**Input**: "quán ăn Đà Nẵng"

**Observation**: LLM nhận ra câu hỏi ngoài phạm vi Hà Nội nhưng không sinh ra `Action:` hay `Action Input:` — thay vào đó trả lời thẳng bằng văn xuôi. Parser regex không tìm thấy pattern → `AGENT_PARSE_ERROR` → prompt không được cập nhật → LLM lặp lại hành vi cũ → đạt `max_steps`.

**Trace từ log (08:43):**

```json
{"event": "AGENT_RUN_START",    "data": {"input": "quán ăn Đà Nẵng", "model": "gpt-4o"}}
{"event": "AGENT_PARSE_ERROR",  "data": {"error": "No Action found", "step": 0}}
{"event": "AGENT_PARSE_ERROR",  "data": {"error": "No Action found", "step": 1}}
{"event": "AGENT_PARSE_ERROR",  "data": {"error": "No Action found", "step": 2}}
{"event": "AGENT_PARSE_ERROR",  "data": {"error": "No Action found", "step": 3}}
{"event": "AGENT_MAX_STEPS_REACHED", "data": {"steps": 5}}
```

**Root Cause**: System prompt thiếu hướng dẫn xử lý edge case ngoài scope — LLM không biết phải gọi `human_escalation_fallback` thay vì trả lời trực tiếp.

**Fix**: Thêm vào system prompt: _"Nếu câu hỏi nằm ngoài phạm vi Hà Nội hoặc không liên quan đến ăn uống, hãy gọi ngay `human_escalation_fallback`."_ Sau khi fix, cùng query chạy lại lúc 08:47 đã gọi đúng tool ngay bước 1.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2 (xử lý out-of-scope)

- **Diff**: Thêm instruction rõ ràng vào system prompt — _"Nếu câu hỏi ngoài phạm vi Hà Nội hoặc không liên quan ẩm thực → gọi `human_escalation_fallback` ngay."_
- **Result**: Query "quán ăn Đà Nẵng" từ loop 5 bước (`AGENT_MAX_STEPS_REACHED`) → xử lý đúng trong 2 bước. Giảm 100% lỗi loop trên loại query này.

### Experiment 2: Chatbot vs Agent — 5 test cases thực tế

| Query                                                | Chatbot                                                     | Agent                                                                                    | Winner    |
| :--------------------------------------------------- | :---------------------------------------------------------- | :--------------------------------------------------------------------------------------- | :-------- |
| "quán ăn ngon"                                       | Trả lời chung chung, không có tên quán cụ thể               | Hỏi lại để làm rõ khu vực                                                                | Draw      |
| "Nhà hàng Pháp Tây Hồ < 500k cho 2 người"            | Gợi ý mơ hồ, có thể hallucinate                             | Trả về đúng 2 quán từ DB (Hoa Sữa 200k, Maison de Hồ Tây 250k)                           | **Agent** |
| "tìm quán chay tại Thanh Xuân"                       | Gợi ý quán chay chung, không xác nhận có ở Thanh Xuân không | Tìm DB → không có → thông báo rõ ràng, gợi ý tìm khu khác                                | **Agent** |
| "tìm sân bóng"                                       | Trả lời ngoài scope nhưng vẫn gợi ý                         | Từ chối đúng scope, không hallucinate                                                    | **Agent** |
| "quán lãng mạn đồ nhật có chỗ để xe đang mở lúc 20h" | Gợi ý 1–2 quán không có nguồn, không kiểm tra giờ           | Tìm → lọc → kiểm tra giờ mở cửa từng quán → trả về Sakura Moon & Kyoto Whisper chính xác | **Agent** |

---

## 6. Production Readiness Review

- **Security**: Tool `_execute_tool` bắt toàn bộ exception và trả về JSON lỗi thay vì expose stack trace. Cần bổ sung input sanitization để tránh prompt injection qua `user_input`.
- **Guardrails**: `max_steps = 5` ngăn vòng lặp vô hạn và giới hạn chi phí tối đa ~$0.09/query. Cần thêm `user_served` flag trong `AGENT_FINISH` để phân biệt "agent chạy xong" vs "user thực sự được phục vụ".
- **Scaling**: Hiện tại conversation history lưu in-memory, mất khi restart. Để production cần persist history ra Redis/DB. Với workflow phức tạp hơn (booking, payment), nên chuyển sang LangGraph để quản lý branching tốt hơn.
