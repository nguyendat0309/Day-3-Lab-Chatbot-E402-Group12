# Trace Report — FoodBot ReAct Agent
## Thông tin chung
- Use case: Tìm quán ăn tại Hà Nội
- Model: gpt-4o (OpenAI)
- MAX_ITERATIONS: 5
- Ngày chạy: 2026-04-06

---

## 1. Success Trace

**Query:** "quán ăn lãng mạn đồ nhật có chỗ để xe đang mở lúc 20h"
**Kết quả:** success
**Số iterations:** 3
**Stopped by:** finish
**Tổng latency:** 2414 + 1929 + 1382 = 5725ms

---

### Step 1

**Thought:**
> "Để đáp ứng yêu cầu của người dùng, tôi cần tìm quán ăn Nhật Bản với không gian lãng mạn và có chỗ để xe tại Hà Nội. Sau đó kiểm tra xem quán đó có mở cửa lúc 20h không."

_Agent decompose query phức tạp (3 tiêu chí: cuisine + ambiance + amenity) và lên kế hoạch 2 bước ngay trong Thought. Không hỏi lại user._

**Action:** `search_restaurants`
**Input:**
```json
{"cuisine": "japanese", "ambiance": "romantic", "amenity": "parking"}
```
**Observation:**
```json
[
  {"id": "r014", "name": "Sakura Moon",   "dish_type": "fine_dining", "district": "Tây Hồ", "price_avg": 290000, "rating": 4.7, "ambiance": "romantic"},
  {"id": "r015", "name": "Kyoto Whisper", "dish_type": "sushi",       "district": "Tây Hồ", "price_avg": 300000, "rating": 4.8, "ambiance": "romantic"}
]
```
**LLM Metric:** latency=2414ms | tokens=1590 | tool_call=0ms

---

### Step 2

**Thought:**
> "Bây giờ, tôi sẽ kiểm tra xem trong các quán ăn vừa tìm được, quán nào mở cửa lúc 20h."

_Agent nhận biết query có giờ cụ thể → bắt buộc gọi `check_open_status` — đúng rule v2. Chọn quán đầu tiên (rating cao nhất) để check._

**Action:** `check_open_status`
**Input:**
```json
{"restaurant_name": "Sakura Moon", "time_str": "20:00"}
```
**Observation:**
```json
{"status": "open", "message": "Restaurant 'Sakura Moon' is OPEN at 20:00 (Operating Hours: 11:00 - 22:00)."}
```
**LLM Metric:** latency=1929ms | tokens=1777 | tool_call=2ms

---

### Step 3

**Thought:**
> "Final Answer: Quán 'Sakura Moon' là một lựa chọn lãng mạn với đồ ăn Nhật Bản và có chỗ để xe. Quán hiện đang mở cửa lúc 20h và nằm ở khu vực Tây Hồ."

**Action:** finish
**Input:**
```json
{"answer": "Quán 'Sakura Moon' là một lựa chọn lãng mạn với đồ ăn Nhật Bản và có chỗ để xe. Quán hiện đang mở cửa lúc 20h (giờ mở: 11:00 - 22:00), nằm ở Tây Hồ. Giá trung bình ~290,000 VND, rating 4.7."}
```
**Observation:** DONE

**LLM Metric:** latency=1382ms | tokens=1866

---

**Nhận xét success trace:**
- **Step 1 — Reasoning tốt nhất**: Agent map đúng 3 tiêu chí phức tạp → params `ambiance: "romantic"`, `amenity: "parking"` — là tính năng mới của v2. v1 không làm được vì thiếu params này.
- **Step 2 — Justify rõ**: Agent tự nhận biết có giờ cụ thể trong query → gọi `check_open_status` đúng rule v2, không bỏ sót bước quan trọng.
- **Step 3**: Dừng đúng lúc sau khi đã có đủ thông tin, answer đầy đủ: tên, giờ mở, giá, rating, quận.
- **v1 sẽ fail**: Không có `ambiance`/`amenity` → search ra kết quả sai. Không check giờ → có thể recommend quán đóng cửa.

---

## 2. Failed Trace — Failure Analysis (Phase 4)

**Query:** "Gợi ý món khi ăn bún bò lần đầu?"
**Kết quả:** fail
**Số iterations:** 5
**Stopped by:** max_iterations

---

### Step 1

**Thought:**
> "Rất tiếc, tôi chỉ hỗ trợ thông tin về các nhà hàng và ẩm thực tại Hà Nội. Bạn có muốn tìm quán ăn không?"

**Action:** _(không có — parse error)_
**Observation:** `AGENT_PARSE_ERROR: No Action found`
**LLM Metric:** latency=969ms | tokens=1594

---

### Step 2

**Thought:**
> "Rất tiếc, tôi chỉ hỗ trợ thông tin về các nhà hàng và ẩm thực tại Hà Nội. Bạn có muốn tìm quán ăn không?"

**Action:** _(không có — parse error)_
**Observation:** `AGENT_PARSE_ERROR: No Action found`
**LLM Metric:** latency=806ms | tokens=1594

---

### Step 3–5 — FAIL POINT

**Thought (step 3, 4, 5 — giống hệt):**
> "Rất tiếc, tôi chỉ hỗ trợ thông tin về các nhà hàng và ẩm thực tại Hà Nội..."

**Observation:**
```json
{"error": "AGENT_PARSE_ERROR: No Action found"}
```
**LLM Metric:** latency: 885ms / 983ms / 840ms | tokens=1594 (không đổi — LLM bị stuck)

---

### Phân tích Failed Trace

| Mục | Nội dung |
|-----|----------|
| Fail ở step | 1 (loop đến step 5) |
| Lý do fail | Agent muốn từ chối nhưng không dùng `Final Answer:` và không có `Action:` → parser không nhận format nào |
| Dấu hiệu trong log | `AGENT_PARSE_ERROR: No Action found` × 5, `tokens=1594` cố định — LLM stuck |
| Root cause (v1) | System prompt chỉ định nghĩa `Thought → Action` nhưng không có escape route khi từ chối |
| Fix áp dụng (v2) | Thêm rule tường minh vào system prompt |
| System prompt v2 | `"QUAN TRỌNG: Nếu câu hỏi KHÔNG liên quan đến nhà hàng hoặc ẩm thực tại Hà Nội → KHÔNG gọi tool. Trả lời ngay bằng Final Answer: Rất tiếc..."` |
| Kết quả sau fix | Query "sân bóng": 1 step, stopped=finish, 0 parse errors, latency=1727ms |

---

## 3. Agent v1 → v2: Các thay đổi thực tế và test case

### Fix 1 — Thought phải viết tiếng Việt

**Vấn đề (v1):**
Log session "một quán ít người ở thanh xuân":
```
[THOUGHT step=1] "The user is asking for a less crowded restaurant in the Thanh Xuân district.
I should search for restaurants in Thanh Xuân and consider capacity..."
```
Thought viết tiếng Anh dù user hỏi tiếng Việt → không nhất quán.

**Fix (v2):** Thêm vào system prompt:
```
- Always think and reason in Vietnamese in every Thought step.
```

**Kết quả sau fix:**
Log session "quán có chỗ để xe":
```
[THOUGHT step=1] "Người dùng muốn tìm quán ăn có chỗ để xe.
Tôi sẽ tìm các nhà hàng với amenity là parking."
```

---

### Fix 2 — Cuisine & dish_type mapping

**Vấn đề (v1):**
Log session "quán phở thanh xuân đang mở":
```json
Action Input: {"cuisine": "vietnamese", "district": "Thanh Xuân"}
```
Search `cuisine: "vietnamese"` trả về cả bún chả, cơm tấm, phở → không lọc đúng món.
Kết quả: "Bún Chả Đắc Kim Nguyễn Trãi" — không phải quán phở.

**Fix (v2):** Thêm `dish_type` param vào `search_restaurants` + mapping trong system prompt:
```
- dish_type mapping: "phở" → "phở", "bún chả" → "bún_chả", "sushi" → "sushi",
  "bbq/nướng hàn" → "bbq", "buffet" → "buffet", "bình dân" → "casual_dining"
- cuisine mapping: phở/bún/cơm → "vietnamese", chay/thuần chay → "vegetarian",
  sushi/ramen → "japanese", kimchi/bbq hàn → "korean"
```

**Kết quả sau fix (v2):**
```json
Action Input: {"cuisine": "vietnamese", "dish_type": "phở", "district": "Thanh Xuân"}
```
→ Filter chính xác, chỉ trả về quán phở thật sự.

---

### Fix 3 — Bắt buộc check giờ mở

**Vấn đề (v1):**
Log session "quán phở thanh xuân đang mở":
```
[THOUGHT step=1] "Tôi cần tìm các quán phở ở quận Thanh Xuân và kiểm tra xem quán nào đang mở."
[TOOL_CALL] tool=search_restaurants input={"cuisine": "vietnamese", "district": "Thanh Xuân"}
[AGENT_FINISH] steps=2, stopped=finish
```
Agent tìm xong → trả Final Answer ngay, **không gọi `check_open_status`** dù query có "đang mở".
Kết quả: Bún Chả Đắc Kim đóng lúc 15:00 nhưng agent không biết và không báo.

**Fix (v2):** Thêm rule vào system prompt:
```
- Nếu user đề cập "đang mở", "còn mở", "mấy giờ mở", hoặc một giờ cụ thể:
  BẮT BUỘC gọi check_open_status sau khi tìm được quán.
```

**Expected flow sau fix (v2):**
```
Step 1: search_restaurants → tìm quán
Step 2: check_open_status("Bún Chả Đắc Kim", "21:00") → {"status": "closed", ...}
Step 3: Final Answer → báo user quán đã đóng, gợi ý quán khác
```

---

### Fix 4 — Thêm dish_type / ambiance / amenity filter vào tool

**Vấn đề (v1):** `search_restaurants` chỉ có 4 params: `cuisine, district, max_price, min_rating`

**Tool spec v1:**
```python
def search_restaurants(cuisine=None, district=None, max_price=None, min_rating=None)
```

**Tool spec v2:**
```python
def search_restaurants(cuisine=None, district=None, dish_type=None,
                       max_price=None, min_rating=None,
                       ambiance=None, amenity=None)
```

**Test case — "quán ăn lãng mạn":**

_v1 — search sai:_
```json
Action Input: {"cuisine": "french"}
```
→ Trả về tất cả quán Pháp, không filter được ambiance.

_v2 — search đúng:_
```json
Action Input: {"ambiance": "romantic"}
```
→ Trả về đúng các quán có `ambiance: "romantic"` từ data (Hoa Sữa, Maison de Hồ Tây, La Serenata...).

**Test case — "quán có chỗ để xe":**

_v1:_ Agent không biết filter gì → trả lời chung chung từ LLM.

_v2:_
```json
Action Input: {"amenity": "parking"}
```
→ Lọc được các quán có `parking` trong data.

**Mapping thêm vào system prompt v2:**
```
- ambiance: "lãng mạn/hẹn hò" → "romantic", "ít người/yên tĩnh/cozy" → "cozy_indoor",
  "sang trọng" → "elegant", "bình dân" → "casual", "vỉa hè" → "street_food_style"
- amenity: "chỗ để xe" → "parking", "nhạc sống" → "live_music",
  "ngoài trời" → "outdoor_seating", "điều hoà" → "air_conditioning"
```

---

## 4. Tổng hợp v1 vs v2

| Bug quan sát trong log (v1) | Fix cụ thể (v2) | Evidence |
|-----------------------------|-----------------|----------|
| Out-of-scope → `PARSE_ERROR` × 5, max_iter | Thêm `Final Answer` rule cho từ chối | Session [19] 5 errors → Session [6] 1 step 0 errors |
| Thought viết tiếng Anh | `"Always think in Vietnamese"` | Session [8] EN → Session [12] VI |
| "quán phở" → search `cuisine: vietnamese` → ra bún chả | Thêm `dish_type` param + cuisine mapping | Tool spec v1 vs v2 |
| Query "đang mở" → không gọi `check_open_status` | Rule bắt buộc check giờ | Session [7] thiếu bước check |
| "quán lãng mạn" / "chỗ để xe" → không filter được | Thêm `ambiance`, `amenity` params + mapping | Tool spec v2 |

---

