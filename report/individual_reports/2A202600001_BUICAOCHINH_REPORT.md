# Báo cáo Cá Nhân (Individual Report)

**Họ và tên:** Bùi Cao Chính
**Nhiệm vụ đảm nhiệm:** Vẽ Flowchart kiến trúc ReAct Agent, Xây dựng giao diện người dùng (UI), hỗ trợ team về GitHub workflow

---

## I. Đóng góp kỹ thuật (15 điểm)

### 1. Thiết kế Flowchart ReAct Agent (`flowchart.md`)
Trực tiếp thiết kế và vẽ toàn bộ sơ đồ hoạt động của hệ thống ReAct Agent bằng Mermaid Diagram, bao gồm các thành phần:
- **Parse intent**: Trích xuất món ăn, địa điểm, constraint từ câu hỏi người dùng; xử lý nhánh "Input mơ hồ" để hỏi lại user.
- **Thought loop**: Vòng lặp chọn tool và xác định tham số, có max iteration = 5 để tránh vòng lặp vô tận.
- **Tool subgraph**: Thể hiện 4 công cụ chính (`search_restaurants`, `get_restaurant_details`, `check_open_status`, `calculate_estimated_cost`) và luồng liên kết giữa chúng.
- **Observation & Decision**: Logic quyết định "Đủ thông tin?" → quay vòng hoặc kết thúc.
- **Fallback node**: Khi vượt max steps thì gọi `human_escalation_fallback()`.

### 2. Xây dựng giao diện Streamlit (`app.py`)
Xây dựng toàn bộ file `app.py` — giao diện web chatbot dùng Streamlit, bao gồm:

- **3 chế độ hiển thị**: So sánh side-by-side, chỉ Agent, chỉ Chatbot — cho phép so sánh trực tiếp hiệu quả của ReAct Agent vs Chatbot Baseline.
- **Provider Factory**: Hàm `create_provider()` tự động khởi tạo LLM đúng loại (Gemini / OpenAI) từ API Key trong `.env`.
- **Sidebar cấu hình**: Dropdown chọn Provider, Model, Slider Max Steps, nút Reset Agent.
- **Realtime stats**: Metric theo dõi số tin nhắn, số yêu cầu của từng mode.
- **Câu hỏi mẫu nhanh**: Sidebar shortcut để test nhanh 5 kịch bản mẫu từ `test_scenarios.py`.
- **Premium UI**: Light theme với gradient background, glassmorphism sidebar, Inter font, color-coded badge cho từng cột.

### 3. Fix bug `chatbot_baseline.py`
Phát hiện và sửa 2 lỗi syntax nghiêm trọng trong file gốc:
- `def init` → `def __init__` (không phải constructor hợp lệ)
- `if name ==` → `if __name__ ==` (không thể chạy trực tiếp file)
- Refactor để nhận `LLMProvider` thay vì hardcode OpenAI, giúp chạy được với cả Gemini.

### 4. Hỗ trợ GitHub workflow cho team
- Fix lỗi import `ModuleNotFoundError: No module named 'src'` trong `tests/test_restaurant_tools.py` bằng cách thêm `sys.path.append(...)` để Python tìm đúng package root.

---

## II. Phân tích lỗi (Debugging Case Study - 10 điểm)

### Lỗi: ImportError khi chạy test từ thư mục `tests/`

**1. Mô tả lỗi:**
Khi chạy lệnh `python tests/test_restaurant_tools.py` từ thư mục gốc, Python báo lỗi:
```
ModuleNotFoundError: No module named 'src'
```
Dù file code nằm đúng vị trí, nhưng Python không tìm thấy package `src`.

**2. Nguyên nhân gốc rễ:**
Python thêm thư mục của file đang chạy (`tests/`) vào `sys.path` — không phải thư mục gốc dự án. Do đó `import src.tools...` không hợp lệ vì `src/` không nằm trong `tests/`.

**3. Cách khắc phục:**
Thêm vào đầu file `test_restaurant_tools.py`:
```python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```
Đoạn này tính đường dẫn tuyệt đối của thư mục cha (`..` từ `tests/` → thư mục gốc) rồi thêm vào `sys.path`, cho Python biết đây là base path để resolve `src`.

**Bài học rút ra:** Khi cấu trúc dự án có nhiều thư mục lồng nhau, cần luôn kiểm tra `sys.path` là điều cần kiểm tra đầu tiên khi gặp `ModuleNotFoundError`.

---

## III. Nhận định cá nhân (10 điểm)

Sự khác biệt lớn nhất về "tư duy" giữa Chatbot thông thường và ReAct Agent — theo quan sát cá nhân khi xây dựng giao diện so sánh — là **khả năng tự nhận biết giới hạn kiến thức của mình**.

Chatbot thông thường hoạt động như một người tự tin thái quá: nó luôn có câu trả lời cho mọi câu hỏi, kể cả khi không có thông tin thực sự. Khi hỏi "Quán Phở Đặc Biệt giờ này có mở cửa không?", Chatbot sẽ đoán và trả lời như thể đó là sự thật — đây là hallucination.

ReAct Agent, ngược lại, có "ý thức" rằng nó cần thông tin xác thực trước khi trả lời. Nó biết: "Tôi cần gọi `check_open_status()` để kiểm tra, tôi không thể đoán mò." Cơ chế Thought-Action-Observation buộc Agent phải trải qua một quy trình xác minh rõ ràng trước khi đưa ra kết luận.

Nói ngắn gọn: Chatbot đang **nói những gì nó nghĩ là đúng**, còn Agent đang **tìm ra sự thật rồi mới nói**.

---

## IV. Đề xuất tương lai (5 điểm)

Nếu có thêm thời gian, tôi sẽ mở rộng dự án theo 2 hướng:

1. **Tích hợp bản đồ tương tác**: Kết nối Google Maps API để hiển thị trực quan vị trí các nhà hàng Agent tìm được ngay trong giao diện chat, thay vì chỉ trả về tên địa chỉ dạng văn bản. Người dùng có thể click vào quán và xem đường đi.

2. **Thêm chức năng đặt bàn**: Tạo thêm tool `book_table(restaurant_name, time, num_people)` tích hợp với một form nhỏ trong UI Streamlit. Sau khi Agent tìm được quán phù hợp, người dùng có thể đặt bàn ngay mà không cần rời ứng dụng — biến đây từ công cụ tư vấn thành một ứng dụng thực tế hoàn chỉnh.
