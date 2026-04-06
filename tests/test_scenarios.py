"""
SKELETON: Bộ 5 kịch bản Test (Dành cho Thành viên 2/4).
Theo Rubric (20đ): Cần có 2 test Chatbot thắng, 2 test Agent thắng, và 1 Edge case.
"""

TEST_SCENARIOS = [
    {
        "id": "chatbot_win_1",
        "description": "Câu hỏi chung chung, không cần tra data (ví dụ: tư vấn phong vị)",
        "query": "Ở Hà Nội thường ăn phở bò hay phở gà? Người Hà Nội hay ăn phở vào lúc nào trong ngày?",
        "expected_winner": "Chatbot",
        "reason": "Chatbot sẽ sinh văn bản mượt hơn. Agent có thể mất thời gian tìm tool vô ích."
    },
    {
        "id": "chatbot_win_2",
        "description": "Định nghĩa ẩm thực/Kiến thức văn hoá",
        "query": "Không gian 'street_food_style' nghĩa là như thế nào đối với văn hoá vỉa hè Việt Nam?",
        "expected_winner": "Chatbot",
        "reason": "Cần lý luận trừu tượng, không tra DB JSON."
    },
    {
        "id": "agent_win_1",
        "description": "Tìm quán ăn phức tạp nhiều điều kiện (Location, Price, Cuisine)",
        "query": "Tôi cần 1 nhà hàng món Pháp ở Tây Hồ, có view Hồ Tây, giá dưới 300k. Nhóm tôi 2 người ăn hết khoảng bao nhiêu?",
        "expected_winner": "Agent",
        "reason": "Chatbot sẽ bịa giá/tên quán. Agent dùng tool check JSON và calculate cost chính xác."
    },
    {
        "id": "agent_win_2",
        "description": "Kiểm tra giờ giấc (Time verification)",
        "query": "Giờ là 21h30 (21:30), tôi muốn ăn Bún chả ở Cầu Giấy, quán 'Bún Chả Cầu Giấy Quán' còn mở cửa không?",
        "expected_winner": "Agent",
        "reason": "Chatbot không biết giờ thực tế của quán. Agent sẽ xài tool 'check_open_status'."
    },
    {
        "id": "edge_case_1",
        "description": "Dữ liệu không tồn tại (Out of domain data)",
        "query": "Tìm cho tôi 5 quán Mexican food ở khu Bách Khoa giá rẻ bèo.",
        "expected_winner": "Agent (với Fallback)",
        "reason": "DB không có Mexican. Chatbot sẽ bịa quán. Agent tìm rỗng -> Phát hiện lỗi -> Gọi tool human_escalation_fallback."
    }
]

def run_evaluation():
    """
    TODO: Cho chạy qua 5 test case bằng cả BaselineChatbot và ReActAgent.
    Đo đạc: Token tiêu thụ, Latency, Số loop của Agent (nếu là Agent).
    """
    print("Bắt đầu chạy Evaluation... (TODO)")

if __name__ == "__main__":
    run_evaluation()
