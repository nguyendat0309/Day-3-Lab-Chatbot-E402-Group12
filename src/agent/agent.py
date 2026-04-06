import os
import json
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.tools import AVAILABLE_TOOLS

class ReActAgent:
    """
    SKELETON: Hanoi Food Expert ReAct Agent
    Thành viên 3 (Core Architect) & 2 (Prompt Engineer) sẽ code chính ở đây.
    """
    
    def __init__(self, llm: LLMProvider, max_steps: int = 5):
        self.llm = llm
        self.tools = AVAILABLE_TOOLS
        self.max_steps = max_steps # Tránh vòng lặp vô hạn
        self.history = []

    def get_system_prompt(self) -> str:
        """
        TODO (Thành viên 2): Viết System Prompt cực kỳ chi tiết.
        1. Role: Local Food Expert tại Hà Nội.
        2. Format bắt buộc: Thought -> Action -> Observation -> Final Answer.
        3. Truyền danh sách API tools (tên tool + docstring) vào prompt để Agent biết cách xài.
        """
        # HINT: Duyệt qua self.tools để in ra tên tool và .__doc__ của tool đó.
        return """
        SKELETON PROMPT: You are a Local Food Expert in Hanoi...
        [TEAM CẦN VIẾT CHI TIẾT PROMPT Ở ĐÂY ĐỂ ĂN 20 ĐIỂM]
        """

    def run(self, user_input: str) -> str:
        """
        TODO (Thành viên 3): Vòng lặp ReAct cốt lõi.
        Mỗi bước (step) cần log lại qua logger.log_event để chấm Traces.
        """
        logger.log_event("AGENT_RUN_START", {"input": user_input, "model": self.llm.model_name})
        
        current_prompt = f"User Request: {user_input}\n"
        steps = 0

        while steps < self.max_steps:
            logger.log_event("AGENT_THINKING", {"step": steps + 1})
            
            # 1. Gọi LLM để sinh ra Thought và Action
            # response = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            
            # 2. TODO: Parse (Bóc tách) Action và Action Input (Param) từ response
            # HINT: Dùng Regex hoặc json để bóc tách. Đừng quên xử lý Exception (try/except)
            
            # 3. TODO: Gọi Tool tương ứng (từ self.tools)
            # observation = self._execute_tool(action_name, action_input)
            
            # 4. Gắn Observation vào current_prompt để LLM đọc ở vòng lặp sau
            
            # 5. Nếu LLM trả về Final Answer -> return kết quả luôn.
            
            steps += 1
            
        # Nếu vượt quá max_steps -> Return Fallback
        logger.log_event("AGENT_MAX_STEPS_REACHED", {"steps": steps})
        return "Xin lỗi, tôi đã mất quá nhiều thời gian suy nghĩ mà chưa ra kết quả. Vui lòng thử lại!"

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Thực thi Tool một cách an toàn.
        """
        logger.log_event("TOOL_CALL", {"tool": tool_name, "args": args})
        
        if tool_name in self.tools:
            try:
                # Gọi hàm
                result = self.tools[tool_name](**args)
                logger.log_event("TOOL_RESULT", {"tool": tool_name, "result_snippet": result[:100]})
                return result
            except Exception as e:
                logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": str(e)})
                return json.dumps({"error": f"Lỗi khi chạy tool: {str(e)}"})
        
        return json.dumps({"error": f"Tool '{tool_name}' không tồn tại!"})
