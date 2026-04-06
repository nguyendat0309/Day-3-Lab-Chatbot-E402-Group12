import os
import json
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker
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
        self.history: List[Dict[str, str]] = []
        self.system_prompt = self.get_system_prompt()

    def get_system_prompt(self) -> str:
        """
        TODO (Thành viên 2): Viết System Prompt cực kỳ chi tiết.
        1. Role: Local Food Expert tại Hà Nội.
        2. Format bắt buộc: Thought -> Action -> Observation -> Final Answer.
        3. Truyền danh sách API tools (tên tool + docstring) vào prompt để Agent biết cách xài.
        """
        # HINT: Duyệt qua self.tools để in ra tên tool và .__doc__ của tool đó.
        tools_desc = "\n".join([f"- {name}: {func.__doc__}" for name, func in self.tools.items()])
        return f"""
You are a Hanoi Food Expert assistant. You are an expert on restaurants and food culture in Hanoi, Vietnam. You help users find the best dining options based on their preferences.

You have access to a set of tools to gather information about restaurants in Hanoi. Use these tools when you need specific data that you don't have.

Always follow this response format:

Thought: [Your reasoning about what information you need and what action to take]
Action: [TOOL_NAME]
Action Input: {{"param1": "value1", "param2": "value2"}}

After you receive the Observation, continue with the next Thought/Action cycle until you have enough information to provide a Final Answer.

When you have all the information needed to answer the user's question, respond with:

Final Answer: [Your complete answer to the user]

Available Tools:
{tools_desc}

Important guidelines:
- Use tools only when necessary. If you can answer directly from your knowledge, do so.
- For restaurant searches, be specific with parameters like cuisine, district, price range.
- Always check opening hours if time is mentioned.
- Calculate costs accurately for groups.
- If no restaurants match the criteria, use the human_escalation_fallback tool.
- Respond in Vietnamese as the user is asking in Vietnamese.
- Be helpful, accurate, and culturally appropriate.
- After gathering all necessary information, provide the Final Answer immediately without further tool calls.
"""

    def run(self, user_input: str) -> str:
        """
        TODO (Thành viên 3): Vòng lặp ReAct cốt lõi.
        Mỗi bước (step) cần log lại qua logger.log_event để chấm Traces.
        """
        logger.log_event("AGENT_RUN_START", {"input": user_input, "model": self.llm.model_name})
        
        history_text = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.history
        ])
        current_prompt = f"{history_text}\nUser Request: {user_input}\n" if self.history else f"User Request: {user_input}\n"
        steps = 0

        while steps < self.max_steps:
            logger.log_event("AGENT_THINKING", {"step": steps + 1})
            
            # 1. Gọi LLM để sinh ra Thought và Action
            response = self.llm.generate(current_prompt, system_prompt=self.system_prompt)
            tracker.track_request(self.llm.provider, self.llm.model_name, response["usage"], response["latency_ms"])
            content = response["content"]
            
            # 2. Kiểm tra nếu có Final Answer
            if "Final Answer:" in content:
                answer = content.split("Final Answer:", 1)[1].strip()
                self.history.append({"role": "user", "content": user_input})
                self.history.append({"role": "assistant", "content": answer})
                # Giữ tối đa 10 lượt gần nhất (20 messages) tránh vượt context window
                self.history = self.history[-20:]
                logger.log_event("AGENT_RUN_END", {"steps": steps, "success": True})
                return answer
            
            # 3. Parse Action và Action Input
            try:
                # Tìm Action
                action_match = re.search(r'Action:\s*(\w+)', content)
                if not action_match:
                    logger.log_event("AGENT_PARSE_ERROR", {"error": "No Action found", "step": steps})
                    steps += 1
                    continue
                
                tool_name = action_match.group(1)
                
                # Tìm Action Input JSON
                json_match = re.search(r'Action Input:\s*(\{[^{}]*\})', content, re.DOTALL)
                if not json_match:
                    logger.log_event("AGENT_PARSE_ERROR", {"error": "No Action Input JSON found", "step": steps})
                    steps += 1
                    continue
                
                action_input_str = json_match.group(1).strip()
                # Loại bỏ markdown nếu có
                action_input_str = action_input_str.strip('`').strip()
                if action_input_str.startswith('json'):
                    action_input_str = action_input_str[4:].strip()
                
                action_input = json.loads(action_input_str)
                
            except Exception as e:
                logger.log_event("AGENT_PARSE_ERROR", {"error": str(e), "step": steps})
                steps += 1
                continue
            
            # 4. Thực thi tool
            observation = self._execute_tool(tool_name, action_input)
            
            # 5. Cập nhật prompt cho vòng lặp tiếp theo
            current_prompt += f"{content}\nObservation: {observation}\n"
            
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
