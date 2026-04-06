## Edge Case — Query ngoài scope (boundary test)

**Query:** "một rạp chiếu phim tại thanh xuân"
**Model:** gpt-4o · **Provider:** OpenAI
**Tổng steps:** 2 · **Stopped by:** finish
**Tổng latency:** 4,674 + 0 + 2,097 = 6,771ms

---

### Step 1 — Thought
**Thought:**
"Người dùng đang tìm kiếm một rạp chiếu phim tại quận
Thanh Xuân, không phải là một nhà hàng. Vì tôi chỉ có
khả năng cung cấp thông tin về các nhà hàng tại Hà Nội,
tôi sẽ cần phải chuyển yêu cầu này tới hỗ trợ của con
người để đảm bảo người dùng nhận được câu trả lời phù
hợp và chính xác."

**Nhận xét:** Thought justify rõ — agent biết mình không
có tool phù hợp, không bịa thông tin.
**Latency:** 4,674ms · tokens: 994

---

### Step 1 — Action
**Action:** human_escalation_fallback
**Input:**
{"reason": "Người dùng yêu cầu thông tin về rạp chiếu
phim tại quận Thanh Xuân, nhưng tôi chỉ có thể cung cấp
thông tin về nhà hàng tại Hà Nội."}

**Observation:**
{"status": "escalated_to_human", "reason": "..."}
**Tool latency:** 0ms (local mock)

---

### Step 2 — Thought
**Thought:**
"Final Answer: Yêu cầu của bạn về một rạp chiếu phim
tại quận Thanh Xuân đã được chuyển tới bộ phận hỗ trợ
khách hàng..."

**Action:** AGENT_FINISH
**Latency:** 2,097ms · tokens: 1,147

---

### Nhận xét

| Tiêu chí | Kết quả |
|----------|---------|
| Boundary detect đúng | ✅ Cinema ≠ restaurant → escalate ngay |
| Không hallucinate | ✅ Không bịa thông tin rạp phim |
| Thought justify rõ | ✅ Giải thích đủ lý do trước khi hành động |
| Escalation message | ✅ Thân thiện, hướng dẫn user chờ support |
| success=true | ⚠️ Flow hoàn thành nhưng user không được served |

**Fix đề xuất:** Thêm field `user_served: false` vào
`AGENT_FINISH` khi stopped_by=escalation để phân biệt
"agent chạy xong" vs "user được giải quyết".