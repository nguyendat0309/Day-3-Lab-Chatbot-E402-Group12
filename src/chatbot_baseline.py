from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class BaselineChatbot:
    """
    SKELETON: Baseline Chatbot (Chỉ gọi LLM 1 lần, không có Tools).
    Dùng để so sánh độ hiệu quả (Latency, Tokens, Độ chính xác) với ReAct Agent.
    """
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def get_system_prompt(self) -> str:
        return """
        Bạn là một trợ lý ảo am hiểu về ẩm thực Hà Nội. 
        Tuy nhiên, bạn chỉ có thể trả lời dựa trên kiến thức có sẵn của bản thân. 
        Bạn không có quyền truy cập Internet hay cơ sở dữ liệu nội bộ.
        """

    def run(self, user_input: str) -> str:
        """
        Xử lý input của người dùng và trả về output trực tiếp từ LLM.
        """
        logger.log_event("BASELINE_START", {"input": user_input, "model": self.llm.model_name})
        
        # TODO: Gọi LLM generate result
        # result = self.llm.generate(user_input, system_prompt=self.get_system_prompt())
        result = "Đây là câu trả lời mẫu của Baseline Chatbot. TODO: Tích hợp API."
        
        logger.log_event("BASELINE_END", {"result_snippet": result[:50]})
        return result
