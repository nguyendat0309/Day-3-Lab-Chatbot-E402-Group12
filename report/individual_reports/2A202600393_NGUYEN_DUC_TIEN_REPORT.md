# Báo cáo Cá Nhân (Individual Report)

**Họ và tên:** Nguyễn Đức Tiến
**MSSV:** 2A202600393
**Nhiệm vụ đảm nhiệm:** Xây dựng ReAct Agent 

---

## I. Đóng góp kỹ thuật (15 điểm)

Các phần tôi trực tiếp xây dựng trong file `src/agent/agentV1.py`:

- **Vòng lặp ReAct (`run` method):** Triển khai vòng lặp Thought → Action → Observation với giới hạn `max_steps = 5` để tránh vòng lặp vô hạn. Mỗi bước đều gọi `logger.log_event` để ghi trace đầy đủ phục vụ chấm điểm và debug.

- **Parser Action/Action Input (`run` method, bước 3):** Dùng `re.search` để bắt `Action: TOOL_NAME` và `Action Input: {...}` từ output thô của LLM. Xử lý thêm trường hợp LLM trả về JSON bọc trong markdown code block (strip backtick và prefix `json`).

- **Thực thi tool an toàn (`_execute_tool` method):** Kiểm tra tool có tồn tại trong `self.tools` không trước khi gọi, bắt exception và trả về JSON lỗi thay vì crash toàn bộ agent.

- **Quản lý conversation history:** Lưu lịch sử hội thoại, cắt giữ tối đa 20 messages gần nhất (`self.history[-20:]`) để tránh vượt context window của LLM.

- **System Prompt (`get_system_prompt` method):** Tự động duyệt `self.tools` để inject tên tool và docstring vào prompt, giúp LLM biết chính xác các tool có sẵn mà không cần hardcode.

---

## II. Phân tích lỗi (Debugging Case Study - 10 điểm)

### Lỗi: Agent rơi vào vòng lặp `AGENT_PARSE_ERROR` liên tục và đạt `MAX_STEPS`

**1. Mô tả lỗi:**

Khi người dùng nhập câu hỏi ngoài phạm vi dữ liệu (ví dụ: "quán ăn Đà Nẵng"), LLM không sinh ra `Action:` hay `Action Input:` mà trả lời thẳng bằng văn xuôi. Parser không tìm thấy pattern → `AGENT_PARSE_ERROR` → bước tiếp theo LLM vẫn nhận cùng prompt cũ → lặp lại lỗi cho đến khi hết `max_steps`.

**2. Dấu vết từ Log (`logs/2026-04-06.log`):**

```json
{"timestamp": "2026-04-06T08:43:39.878615", "event": "AGENT_RUN_START", "data": {"input": "quán ăn Đà Nẵng", "model": "gpt-4o"}}
{"timestamp": "2026-04-06T08:43:41.365899", "event": "AGENT_PARSE_ERROR", "data": {"error": "No Action found", "step": 0}}
{"timestamp": "2026-04-06T08:43:42.392436", "event": "AGENT_PARSE_ERROR", "data": {"error": "No Action found", "step": 1}}
{"timestamp": "2026-04-06T08:43:43.361484", "event": "AGENT_PARSE_ERROR", "data": {"error": "No Action found", "step": 2}}
{"timestamp": "2026-04-06T08:43:44.436274", "event": "AGENT_PARSE_ERROR", "data": {"error": "No Action found", "step": 3}}
{"timestamp": "2026-04-06T08:43:45.536042", "event": "AGENT_MAX_STEPS_REACHED", "data": {"steps": 5}}
```

Có thể thấy rõ: 5 bước liên tiếp đều parse lỗi, không có `TOOL_CALL` nào, kết thúc bằng `AGENT_MAX_STEPS_REACHED`. Tổng chi phí lãng phí ~0.07 USD chỉ cho một câu hỏi không hợp lệ.

**3. Cách khắc phục:**

- **Ngắn hạn:** Thêm vào system prompt hướng dẫn rõ: _"Nếu câu hỏi nằm ngoài phạm vi Hà Nội, hãy gọi ngay `human_escalation_fallback` thay vì trả lời trực tiếp."_ Sau khi sửa prompt, agent đã gọi đúng tool (xem log `08:47:47` – cùng input "quán ăn Đà Nẵng" nhưng lần này gọi `human_escalation_fallback` thành công ngay bước 1).

- **Dài hạn:** Khi `AGENT_PARSE_ERROR` xảy ra, thêm vào `current_prompt` một dòng nhắc nhở: `"[System: Lần trước không tìm thấy Action. Hãy dùng đúng format: Action: TOOL_NAME]"` để LLM tự điều chỉnh thay vì lặp lại lỗi.

---

## III. Nhận định cá nhân (10 điểm)

Chatbot thông thường (Phase 1) hoạt động theo kiểu **phản xạ một chiều**: nhận câu hỏi → tra kiến thức đã có → trả lời. Nó không biết mình đang thiếu thông tin gì, và cũng không có cách nào đi lấy thêm dữ liệu.

Agent (Phase 2) thì khác ở chỗ nó **biết mình không biết**. Trước khi trả lời, nó tự hỏi: "Mình cần thông tin gì? Mình có tool nào để lấy không?" Rồi nó hành động, quan sát kết quả, và điều chỉnh suy nghĩ tiếp theo. Đây là tư duy **lập kế hoạch và phản hồi vòng lặp** – gần với cách con người giải quyết vấn đề hơn là chỉ nhớ và đọc lại.

Nói đơn giản: chatbot _trả lời_, còn agent _giải quyết vấn đề_.

---

## IV. Đề xuất tương lai (5 điểm)

Nếu có thêm thời gian, tôi sẽ bổ sung **bộ nhớ dài hạn (long-term memory)** cho agent. Hiện tại, lịch sử hội thoại bị cắt sau 20 messages và mất hoàn toàn khi restart. Nếu tích hợp một vector store đơn giản (như ChromaDB), agent có thể nhớ sở thích của từng người dùng qua nhiều phiên – ví dụ: biết rằng người dùng này hay ăn chay, hay tìm quán ở Tây Hồ – và đưa ra gợi ý cá nhân hóa hơn mà không cần hỏi lại từ đầu.
