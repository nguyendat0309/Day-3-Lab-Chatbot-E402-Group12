from src.core.llm_provider import LLMProvider

class BaselineChatbot:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.history = []

    def get_system_prompt(self) -> str:
        return """Bạn là một trợ lý ảo am hiểu về ẩm thực Hà Nội.
Tuy nhiên, bạn chỉ có thể trả lời dựa trên kiến thức có sẵn của bản thân.
Bạn không có quyền truy cập Internet hay cơ sở dữ liệu nội bộ nào.
Trả lời bằng tiếng Việt, ngắn gọn và hữu ích."""

    def run(self, user_input: str) -> str:
        history_text = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.history
        ])
        prompt = f"{history_text}\nUSER: {user_input}" if self.history else user_input

        response = self.llm.generate(prompt, system_prompt=self.get_system_prompt())
        answer = response["content"].strip()

        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": answer})
        self.history = self.history[-20:]
        return answer

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    from src.core.openai_provider import OpenAIProvider
    llm = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
    chatbot = BaselineChatbot(llm)

    print("=== Baseline Chatbot ===")
    while True:
        user_input = input("Bạn: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        answer = chatbot.run(user_input)
        print("Chatbot:", answer)
