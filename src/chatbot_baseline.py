import os
from openai import OpenAI

class BaselineChatbot:
    def init(self, api_key: str):
        # Khởi tạo client OpenAI
        self.client = OpenAI(api_key=api_key)

    def get_system_prompt(self) -> str:
        return """
        Bạn là một trợ lý ảo am hiểu về ẩm thực Hà Nội.
        Tuy nhiên, bạn chỉ có thể trả lời dựa trên kiến thức có sẵn của bản thân.
        Bạn không có quyền truy cập Internet hay cơ sở dữ liệu nội bộ.
        """

    def run(self, user_input: str, data: str = "") -> str:
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"Data: {data}\nQuestion: {user_input}"}
            ]
        )
        # Lấy text trả về
        return response.choices[0].message.content.strip()

if name == 'main':
    api_key = ""
    chatbot = BaselineChatbot(api_key)

    print("=== Baseline Chatbot ===")
    while True:
        user_input = input("Bạn: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        # Giả sử data rỗng lúc test
        answer = chatbot.run(user_input, data="")
        print("Chatbot:", answer)
