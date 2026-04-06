# Trace Report — FoodBot ReAct Agent

## Thông tin chung
- Use case: Tìm quán ăn cá nhân hoá
- Model: claude-sonnet-4-5
- MAX_ITERATIONS: 5
- Ngày chạy: [điền sau]

---

## 1. Success Trace

**Query:** "Tìm quán chay, gần đây, còn mở 9 tối, budget 80k"
**Kết quả:** [success / fail]
**Số iterations:** [điền sau]
**Stopped by:** finish

---

### Step 1
**Thought:**
[copy từ log — phải giải thích tại sao chọn action này]

**Action:** [tên tool]
**Input:**
```json
[copy từ log]
```
**Observation:**
```json
[copy từ log — tóm tắt nếu dài]
```

---

### Step 2
**Thought:**
[copy từ log]

**Action:** [tên tool]
**Input:**
```json
[copy từ log]
```
**Observation:**
```json
[copy từ log]
```

---

### Step 3
**Thought:**
[copy từ log — giải thích tại sao đủ thông tin để finish]

**Action:** finish
**Input:**
```json
{"answer": "[copy câu trả lời cuối]"}
```
**Observation:** DONE

**Nhận xét success trace:**
- Thought justify rõ ở bước nào?
- Bước nào agent reasoning tốt nhất?
- Có bước nào dư thừa không?

---

## 2. Failed Trace

**Query:** "[query mà agent sẽ fail — lấy từ P4]"
**Kết quả:** fail
**Số iterations:** [điền sau]
**Stopped by:** [max_iterations / error / wrong_tool]

---

### Step 1
**Thought:**
[copy từ log]

**Action:** [tên tool]
**Input:**
```json
[copy từ log]
```
**Observation:**
```json
[copy từ log]
```

---

### Step [N] — FAIL POINT
**Thought:**
[copy từ log]

**Action:** [action sai]
**Input:**
```json
[copy — chỗ này có thể thấy hallucinated args]
```
**Observation:**
```json
{"error": "[tool error message]"}
```

---

### Phân tích failed trace

| Mục | Nội dung |
|-----|----------|
| Fail ở step | [số] |
| Lý do fail | [agent chọn sai tool / hallucinate args / loop vô hạn / ...] |
| Dấu hiệu trong log | [copy dòng log cụ thể] |
| Fix đề xuất | [thêm rule vào system prompt / sửa tool description / ...] |
| System prompt v2 | [dòng cần thêm vào prompt] |

---

## 3. Provider Comparison

**Query dùng để test:** "Tìm quán chay, gần đây, còn mở 9 tối, budget 80k"

| Bước | Claude (s) | OpenAI (s) |
|------|-----------|-----------|
| Thought 1 | | |
| Tool call 1 | | |
| Thought 2 | | |
| Tool call 2 | | |
| Finish | | |
| **Tổng** | | |

**Chất lượng output:**

| Tiêu chí | Claude | OpenAI |
|----------|--------|--------|
| Thought justify rõ | | |
| Chọn tool đúng | | |
| Answer đầy đủ | | |
| Có warning cụ thể | | |

**Kết luận:**
- Provider nào nhanh hơn?
- Provider nào reasoning rõ hơn?
- Khuyến nghị dùng provider nào cho use case này?

---

## 4. Checklist nộp bài

- [ ] Success trace đủ 3+ steps, mỗi Thought justify rõ
- [ ] Failed trace có phân tích lý do + fix đề xuất
- [ ] Provider table có số latency thật từ logs
- [ ] processed_data.json chạy được