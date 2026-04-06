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

### Case Study 1: Agent loop vô hạn khi query ngoài scope — "Gợi ý món khi ăn bún bò lần đầu?"

**Input**: "Gợi ý món khi ăn bún bò lần đầu?"

**Observation**: LLM nhận ra câu hỏi ngoài scope nhưng chỉ viết text thuần — không dùng `Final Answer:` và không có `Action:`. Parser regex không tìm thấy pattern nào → `AGENT_PARSE_ERROR` × 5 → đạt `max_steps`, trả về fallback rỗng.

**Trace từ log (2026-04-06):**

```json
{"event": "AGENT_RUN_START",   "data": {"input": "Gợi ý món khi ăn bún bò lần đầu?", "model": "gpt-4o"}}
{"event": "LLM_METRIC",        "data": {"latency_ms": 969,  "total_tokens": 1594}}
{"event": "AGENT_PARSE_ERROR", "data": {"error": "No Action found", "step": 1}}
{"event": "LLM_METRIC",        "data": {"latency_ms": 806,  "total_tokens": 1594}}
{"event": "AGENT_PARSE_ERROR", "data": {"error": "No Action found", "step": 2}}
{"event": "LLM_METRIC",        "data": {"latency_ms": 885,  "total_tokens": 1594}}
{"event": "AGENT_PARSE_ERROR", "data": {"error": "No Action found", "step": 3}}
{"event": "LLM_METRIC",        "data": {"latency_ms": 983,  "total_tokens": 1594}}
{"event": "AGENT_PARSE_ERROR", "data": {"error": "No Action found", "step": 4}}
{"event": "LLM_METRIC",        "data": {"latency_ms": 840,  "total_tokens": 1594}}
{"event": "AGENT_PARSE_ERROR", "data": {"error": "No Action found", "step": 5}}
{"event": "AGENT_FINISH",      "data": {"total_steps": 5, "stopped_by": "max_iter", "answer_preview": ""}}
```

**Dấu hiệu nhận biết**: `total_tokens=1594` không đổi qua 5 steps → LLM đang trả lời giống hệt nhau, không nhận được feedback từ Observation.

**Root Cause**: System prompt v1 chỉ định nghĩa `Thought → Action → Observation` nhưng **không có escape route** — LLM không biết phải dùng `Final Answer:` khi muốn từ chối.

**Fix áp dụng (v2)**: Thêm rule tường minh vào system prompt:
```
QUAN TRỌNG: Nếu câu hỏi KHÔNG liên quan đến nhà hàng hoặc ẩm thực tại Hà Nội
→ KHÔNG gọi bất kỳ tool nào. Trả lời ngay bằng:
Final Answer: "Rất tiếc, tôi chỉ hỗ trợ thông tin về các nhà hàng và ẩm thực tại Hà Nội."
```

**Kết quả sau fix**: Query "sân bóng" → 1 step, `stopped_by=finish`, 0 parse errors, latency=1727ms.

---

### Case Study 2: Hallucinated argument — "t đói"

**Input**: "t đói" (không đề cập district)

**Trace từ log:**
```json
{"event": "TOOL_CALL", "data": {"step": 2, "tool": "search_restaurants",
  "input": {"district": "Thanh Xuân", "min_rating": 4.0}}}
```

**Vấn đề**: Agent tự điền `district: "Thanh Xuân"` không có trong query — hallucinated từ context history session trước. Kết quả chỉ trả về 1 quán (r028) thay vì 30 quán toàn Hà Nội.

**Root Cause**: `self.history` giữ lại context từ session trước → nhiễm vào Thought của session hiện tại.

**Fix áp dụng (v2)**:
```
- Không tự suy luận district nếu user không đề cập rõ ràng.
  Để trống để tìm toàn bộ Hà Nội.
```

---

### Case Study 3: Thiếu `check_open_status` dù query có giờ cụ thể — "quán phở thanh xuân đang mở"

**Input**: "quán phở thanh xuân đang mở"

**Trace từ log:**
```json
{"event": "TOOL_CALL", "data": {"tool": "search_restaurants",
  "input": {"cuisine": "vietnamese", "district": "Thanh Xuân"}}}
{"event": "AGENT_FINISH", "data": {"total_steps": 2, "stopped_by": "finish"}}
```

**Vấn đề**: Agent tìm xong → trả Final Answer ngay mà không gọi `check_open_status`. Bún Chả Đắc Kim đóng lúc 15:00 nhưng agent không biết và không cảnh báo user.

**Root Cause**: System prompt v1 chỉ nói "Always check opening hours if time is mentioned" nhưng không đủ mạnh để enforce.

**Fix áp dụng (v2)**:
```
- Nếu user đề cập "đang mở", "còn mở", "mấy giờ mở", hoặc một giờ cụ thể:
  BẮT BUỘC gọi check_open_status sau khi tìm được quán.
```

---

## 5. Ablation Studies & Experiments

### Experiment 1: System Prompt v1 vs v2 — Out-of-scope handling

| | Agent v1 | Agent v2 |
|--|---------|---------|
| **Query** | "Gợi ý món khi ăn bún bò lần đầu?" | "Gợi ý món khi ăn bún bò lần đầu?" |
| **Steps** | 5 (max_iter) | 1 |
| **Parse errors** | 5 | 0 |
| **Total tokens** | 1594 × 5 = 7970 | 1594 |
| **Stopped by** | max_iterations | finish |
| **Answer** | "" (rỗng) | "Rất tiếc, tôi chỉ hỗ trợ..." |
| **Diff** | Không có escape route | Thêm `Final Answer` rule cho từ chối |

**Kết quả**: Giảm 100% lỗi loop, tiết kiệm 5× token trên loại query này.

---

### Experiment 2: Tool spec v1 vs v2 — dish_type + ambiance + amenity filter

**Query**: "quán ăn lãng mạn đồ nhật có chỗ để xe đang mở lúc 20h"

| | Tool v1 | Tool v2 |
|--|---------|---------|
| **Params có sẵn** | `cuisine, district, max_price, min_rating` | + `dish_type, ambiance, amenity` |
| **Tool call** | `{"cuisine": "japanese"}` | `{"cuisine": "japanese", "ambiance": "romantic", "amenity": "parking"}` |
| **Kết quả search** | Tất cả quán Nhật (4 quán, bao gồm không lãng mạn) | Chỉ quán Nhật + lãng mạn + parking (2 quán chính xác) |
| **check_open_status** | Không gọi | Gọi đúng → xác nhận Sakura Moon OPEN 20:00 |
| **Answer chất lượng** | Thiếu ambiance/amenity filter, không check giờ | Đúng 100% tiêu chí user yêu cầu |

**Mapping mới trong system prompt v2:**
```
dish_type:  "phở" → "phở" | "bún chả" → "bún_chả" | "sushi" → "sushi" | "bbq" → "bbq"
ambiance:   "lãng mạn" → "romantic" | "yên tĩnh" → "cozy_indoor" | "sang trọng" → "elegant"
amenity:    "chỗ để xe" → "parking" | "nhạc sống" → "live_music" | "ngoài trời" → "outdoor_seating"
```

---

### Experiment 3: Chatbot vs Agent — 5 test cases thực tế

| Query | Chatbot | Agent v2 | Winner |
| :---- | :------ | :------- | :----- |
| "quán ăn ngon" | Trả lời chung chung, không có tên quán cụ thể | Hỏi lại để làm rõ khu vực | Draw |
| "Nhà hàng Pháp Tây Hồ < 500k cho 2 người" | Gợi ý mơ hồ, có thể hallucinate | Trả về đúng 2 quán từ DB (Hoa Sữa 200k, Maison de Hồ Tây 250k) | **Agent** |
| "tìm quán chay tại Thanh Xuân" | Gợi ý quán chay chung, không xác nhận | Tìm DB → không có → thông báo rõ, gợi ý khu khác | **Agent** |
| "tìm sân bóng" | Trả lời ngoài scope, vẫn gợi ý | Từ chối đúng scope, 1 step, không hallucinate | **Agent** |
| "quán lãng mạn đồ nhật có chỗ để xe đang mở lúc 20h" | Gợi ý 1–2 quán không nguồn, không check giờ | search → filter ambiance/amenity → check_open_status → Sakura Moon chính xác | **Agent** |

---

## 6. Production Readiness Review

- **Security**: Tool `_execute_tool` bắt toàn bộ exception và trả về JSON lỗi thay vì expose stack trace. Cần bổ sung input sanitization để tránh prompt injection qua `user_input`.
- **Guardrails**: `max_steps = 5` ngăn vòng lặp vô hạn và giới hạn chi phí tối đa ~$0.09/query. Cần thêm `user_served` flag trong `AGENT_FINISH` để phân biệt "agent chạy xong" vs "user thực sự được phục vụ".
- **Scaling**: Hiện tại conversation history lưu in-memory, mất khi restart. Để production cần persist history ra Redis/DB. Với workflow phức tạp hơn (booking, payment), nên chuyển sang LangGraph để quản lý branching tốt hơn.
