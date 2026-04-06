# Báo cáo Cá Nhân (Individual Report)

**Họ và tên:** Nguyễn Tiến Đạt  
**Nhiệm vụ đảm nhiệm:** Mock data và xây dựng code base

## I. Đóng góp kỹ thuật (15 điểm)
Liệt kê chi tiết những đoạn code, module, hoặc công cụ mà BẠN TRỰC TIẾP xây dựng.

### 1. Xây dựng Mock Data
- Đã xây dựng file `restaurants_hanoi.json` chứa dữ liệu mẫu của 20+ nhà hàng tại Hà Nội với đầy đủ thông tin:
  - Tên nhà hàng, địa chỉ, quận/huyện
  - Loại ẩm thực (cuisine_type)
  - Khoảng giá (price_range)
  - Đánh giá (rating)
  - Các món ăn đặc trưng (specialties)
  - Tiện ích (amenities)
  - Giờ mở cửa (opening_hours)

### 2. Xây dựng Code Base
- Đã code file `restaurant_tools.py` bao gồm các tool functions:
  - `search_restaurants()`: Tìm kiếm nhà hàng theo cuisine, quận, và khoảng giá
  - `get_restaurant_details()`: Lấy thông tin chi tiết của một nhà hàng
  - `calculate_estimated_cost()`: Tính toán chi phí ước tính cho nhóm
  - Xử lý các trường hợp edge case và validation

- Đã thiết lập cấu trúc project:
  - File `requirements.txt` với các dependencies cần thiết
  - File `app.py` với cấu hình agent cơ bản
  - Tích hợp LangChain và OpenAI API

### 3. Đóng góp khác
- Thiết lập môi trường development và testing
- Viết docstring chi tiết cho các functions
- Đảm bảo code tuân thủ Python best practices

## II. Phân tích lỗi (Debugging Case Study - 10 điểm)

### 1. Mô tả lỗi
Trong quá trình phát triển, Agent gặp lỗi khi parse kết quả JSON từ function `search_restaurants()`. Agent trả về lỗi "JSONDecodeError" hoặc bị confuse khi không có nhà hàng nào match với tiêu chí tìm kiếm.

### 2. Dấu vết từ Log
```json
{
  "timestamp": "2024-XX-XX",
  "action": "search_restaurants",
  "input": {
    "cuisine": "Ý",
    "district": "Hoàn Kiếm",
    "max_price": 100000
  },
  "output": [],
  "error": "Agent attempted to access restaurant details from empty result"
}
```

### 3. Cách khắc phục
- **Giải pháp 1**: Thêm validation và error handling trong function `search_restaurants()`:
  - Kiểm tra nếu kết quả rỗng, trả về message thông báo rõ ràng
  - Normalize input data (lowercase, strip whitespace)
  
- **Giải pháp 2**: Cải thiện docstring của tool để Agent hiểu rõ hơn:
  - Mô tả rõ format của output
  - Đưa ra ví dụ cụ thể về cách sử dụng
  - Giải thích các trường hợp edge case

- **Giải pháp 3**: Thêm fallback logic:
  - Nếu không tìm thấy kết quả chính xác, suggest các nhà hàng tương tự
  - Relax một số constraints (ví dụ: tăng price_range)

## III. Nhận định cá nhân (10 điểm)

Từ góc nhìn của tôi, sự khác biệt lớn nhất về "Tư duy" giữa Chatbot thông thường (Phase 1) và Agent (Phase 2) là:

**Chatbot Phase 1** hoạt động theo kiểu "phản xạ" - nhận input và generate output dựa trên pattern đã học, không có khả năng tương tác với thế giới bên ngoài. Nó chỉ có thể trả lời dựa trên kiến thức được training sẵn.

**Agent Phase 2** có tư duy "chủ động và có mục tiêu" (goal-oriented):
- **Planning**: Agent có khả năng phân tích yêu cầu và lập kế hoạch từng bước
- **Tool Use**: Biết khi nào cần dùng tool nào để đạt được mục tiêu
- **Reasoning**: Có khả năng suy luận qua nhiều bước (multi-step reasoning)
- **Adaptation**: Điều chỉnh hành động dựa trên kết quả của bước trước

Ví dụ: Khi user hỏi "Tìm nhà hàng Nhật giá rẻ gần Hồ Gươm", Agent sẽ:
1. Hiểu "gần Hồ Gươm" = Hoàn Kiếm district
2. "Giá rẻ" = price_range thấp
3. Gọi tool `search_restaurants()` với params phù hợp
4. Nếu không có kết quả, relax constraints và thử lại
5. Present kết quả theo format dễ hiểu

## IV. Đề xuất tương lai (5 điểm)

Nếu có thêm thời gian hoặc phát triển thành đồ án, tôi sẽ mở rộng các tính năng sau:

### 1. Tích hợp Real-time Data
- Kết nối API của Google Maps/Foursquare để lấy data thực tế
- Cập nhật thông tin giờ mở cửa, đánh giá real-time
- Hiển thị khoảng cách và thời gian di chuyển từ vị trí hiện tại

### 2. Personalization
- Lưu lịch sử preferences của user (món ăn yêu thích, ngân sách, vị trí thường xuyên)
- Recommendation system dựa trên collaborative filtering
- Học từ feedback của user để cải thiện suggestions

### 3. Multi-modal Features
- Hỗ trợ image search: user upload ảnh món ăn, agent tìm nhà hàng có món đó
- Voice interface: tích hợp speech-to-text và text-to-speech
- Hiển thị map và hình ảnh nhà hàng

### 4. Advanced Planning
- So sánh nhiều nhà hàng theo multiple criteria
- Lên lịch đặt bàn tự động
- Gợi ý combo nhà hàng cho cả ngày (sáng-trưa-tối)
- Tính toán route optimization khi đi nhiều địa điểm

### 5. Social Features
- Tích hợp review từ cộng đồng
- Cho phép user chia sẻ wishlist/favorites
- Group decision making: poll nhóm bạn để chọn nhà hàng
