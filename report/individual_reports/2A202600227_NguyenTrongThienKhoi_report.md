# Báo cáo Cá Nhân (Individual Report)

**Họ và tên:** Nguyễn Trọng Thiên Khôi
**Mã sinh viên:** 2A202600227
**Nhiệm vụ đảm nhiệm:** Telemetry & Logging, Agent v2 Improvement, Tool Design Evolution, Trace Analysis

---

## I. Đóng góp kỹ thuật (15 điểm)

### 1. Cải tiến Telemetry — `src/telemetry/logger.py`

Thêm 2 method mới để log đầy đủ từng bước ReAct loop:

```python
def log_thought(self, step: int, thought: str):
    self.log_event("AGENT_THOUGHT", {"step": step, "thought": thought})

def log_tool_call(self, step: int, tool: str, tool_input: dict, observation: str):
    self.log_event("TOOL_CALL", {
        "step": step, "tool": tool,
        "input": tool_input, "observation": observation[:300]
    })
```

Trước khi thêm, log chỉ có `TOOL_CALL` chứa tên tool — không có Thought text và không có input args. Sau khi thêm, đủ data để copy vào trace.md.

### 2. Thêm per-step latency — `src/telemetry/metrics.py`

```python
def track_step(self, step: int, phase: str, provider: str, latency_ms: int):
    # phase: "thought" | "tool_call"
    metric = {"step": step, "phase": phase, "provider": provider, "latency_ms": latency_ms}
    self.session_metrics.append(metric)
    logger.log_event("STEP_LATENCY", metric)
```

Cần thiết để điền bảng latency per-step trong trace.md phần Provider Comparison.

### 3. Tích hợp telemetry vào Agent — `src/agent/agent.py`

Sửa `run()` để gọi đầy đủ các method telemetry mới, và sửa `_execute_tool()` trả về `Tuple[str, bool]` để có success flag:

```python
# Parse và log Thought
thought_match = re.search(r'Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)', content, re.DOTALL)
thought_text = thought_match.group(1).strip() if thought_match else content.strip()
logger.log_thought(step_num, thought_text)

# Đo tool latency
t0 = time.time()
observation, success = self._execute_tool(tool_name, action_input)
tool_latency_ms = int((time.time() - t0) * 1000)

logger.log_tool_call(step_num, tool_name, action_input, observation)
logger.log_tool_result(step_num, tool_name, success, observation)
tracker.track_step(step_num, "tool_call", self.llm.provider, tool_latency_ms)
```

### 4. Mở rộng tool `search_restaurants` — `src/tools/restaurant_tools.py`

Thêm 3 params mới để filter chính xác hơn:

```python
def search_restaurants(
    cuisine=None, district=None, max_price=None, min_rating=None,
    dish_type=None,   # "phở", "bún_chả", "sushi", "bbq", "buffet"...
    ambiance=None,    # "romantic", "cozy_indoor", "elegant", "casual"...
    amenity=None      # "parking", "live_music", "outdoor_seating"...
) -> str:
```

Kết quả trả về cũng bổ sung `dish_type` và `ambiance` để agent có đủ thông tin recommend.

### 5. Cải tiến System Prompt v1 → v2 — `src/agent/agent.py`

Thêm 4 rules mới dựa trên phân tích log:
- `"Always think and reason in Vietnamese in every Thought step"`
- Bảng mapping cuisine/dish_type/ambiance/amenity
- Rule bắt buộc `check_open_status` khi có giờ cụ thể
- Rule `Final Answer` khi query ngoài domain

### 6. Web Demo — `app.py`

Xây dựng Streamlit app có 3 mode: Chatbot, Agent, So sánh song song — dùng để demo live cho instructor.

---

## II. Phân tích lỗi (Debugging Case Study - 10 điểm)

### Lỗi: Agent loop vô hạn khi query ngoài scope

**1. Mô tả lỗi:**
Query "Gợi ý món khi ăn bún bò lần đầu?" khiến agent lặp 5 bước liên tiếp rồi trả về answer rỗng. User không nhận được phản hồi gì.

**2. Dấu vết từ Log:**

Mở `logs/2026-04-06.log`, tìm event `AGENT_RUN_START` với input trên:

```json
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

**Dấu hiệu quan trọng**: `total_tokens=1594` không đổi qua tất cả 5 steps → LLM đang trả lời giống hệt nhau mỗi bước, không nhận được feedback từ Observation. Đây là dấu hiệu của infinite loop.

**3. Cách khắc phục:**

Đọc response thực tế của LLM từ log `AGENT_THOUGHT`:
```
"Rất tiếc, tôi chỉ hỗ trợ thông tin về các nhà hàng và ẩm thực tại Hà Nội..."
```

LLM **biết** đây là out-of-scope và muốn từ chối, nhưng nó viết text thuần — không có `Action:` và không có `Final Answer:`. Parser regex tìm không ra pattern nào → parse error → prompt không update → LLM lặp lại y chang.

**Root cause**: System prompt v1 chỉ định nghĩa flow `Thought → Action → Observation` nhưng không có escape route cho trường hợp từ chối.

**Fix áp dụng vào system prompt v2:**
```
QUAN TRỌNG: Nếu câu hỏi KHÔNG liên quan đến nhà hàng hoặc ẩm thực tại Hà Nội
(ví dụ: sân bóng, khách sạn, thời tiết...) → KHÔNG gọi bất kỳ tool nào.
Trả lời ngay bằng Final Answer: "Rất tiếc, tôi chỉ hỗ trợ thông tin về
các nhà hàng và ẩm thực tại Hà Nội. Bạn có muốn tìm quán ăn không?"
```

**Kết quả sau fix**: Query "sân bóng" → 1 step, `stopped_by=finish`, 0 parse errors, latency=1727ms — giảm từ 5 steps xuống 1 step và tiết kiệm 5× token.

---

## III. Nhận định cá nhân (10 điểm)

Sự khác biệt lớn nhất giữa Chatbot và ReAct Agent không phải ở kết quả trả về — mà ở **cách tiếp cận vấn đề**.

Chatbot hoạt động như một người trả lời từ trí nhớ: nhận câu hỏi → tổng hợp kiến thức đã có → trả lời. Nó không biết mình đúng hay sai vì không có cách kiểm chứng. Khi hỏi "Nhà hàng Pháp Tây Hồ dưới 500k", chatbot có thể đưa ra tên quán nghe có vẻ hợp lý nhưng thực ra không tồn tại, hoặc giá đã lỗi thời — và nó không biết điều đó.

Agent hoạt động theo kiểu **plan → act → observe → adjust**: mỗi bước đều có lý do rõ ràng trong Thought, mỗi hành động đều được kiểm chứng bằng Observation thực tế từ tool. Khi search không ra kết quả, agent biết ngay và có thể thử lại với tiêu chí khác, hoặc escalate — thay vì bịa thông tin.

Điều tôi thấy rõ nhất qua lab này: với query phức tạp như "quán lãng mạn đồ nhật có chỗ để xe đang mở lúc 20h", chatbot trả lời trong 1 lần gọi LLM nhưng không thể verify được gì. Agent mất 3 bước (search → check_open → final answer) và chậm hơn 2× — nhưng kết quả chính xác 100% vì từng bước đều dựa trên data thật.

Với các use case cần độ chính xác cao (đặt bàn, kiểm tra giờ mở, tính chi phí), agent là lựa chọn bắt buộc. Với câu hỏi đơn giản không cần data thật, chatbot nhanh và rẻ hơn — đây là lý do trong thực tế người ta thường kết hợp cả hai.

---

## IV. Đề xuất tương lai (5 điểm)

**1. RAG thay vì JSON tĩnh**

Hiện tại data là file `restaurants_hanoi.json` với 30 quán — cứng và không update được. Production cần kết nối với database thật (PostgreSQL) và dùng vector search (pgvector / Qdrant) để tìm quán theo semantic query như "quán có không khí giống Hội An" thay vì chỉ filter exact match.

**2. Multi-agent với booking tool**

Thêm agent thứ 2 chuyên xử lý đặt bàn: khi FoodAgent tìm được quán phù hợp, nó pass sang BookingAgent để check slot trống và xác nhận đặt chỗ. Dùng LangGraph để quản lý handoff giữa các agent — tránh 1 agent ôm quá nhiều tools.

**3. User profile & personalization**

Lưu lịch sử query và preference của từng user (cuisine ưa thích, budget thường, khu vực hay ăn) vào Redis. Agent dùng profile này để filter mặc định mà không cần user phải nói rõ mỗi lần — giống recommendation system nhưng driven bởi agent reasoning.

**4. Guardrails & retry logic**

Thêm retry khi tool call fail (network timeout, API lỗi) với exponential backoff. Thêm `user_served` flag vào `AGENT_FINISH` để phân biệt "agent chạy xong" vs "user thực sự được phục vụ" — hiện tại escalation cũng bị log là `stopped_by=finish` dù user chưa có câu trả lời thật.
