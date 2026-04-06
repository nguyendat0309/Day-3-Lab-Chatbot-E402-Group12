import json
import re
import time
from typing import List, Dict, Any, Tuple
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
- Always think and reason in Vietnamese in every Thought step.
- Use tools only when necessary. If you can answer directly from your knowledge, do so.
- For restaurant searches, be specific with parameters like cuisine, district, price range.
- Cuisine mapping: phở/bún/cơm/bánh mì/Vietnamese = "vietnamese", sushi/ramen = "japanese", pizza/pasta = "italian", kimchi/bbq hàn = "korean", croissant/bistro = "french", hải sản = "seafood", chay/thuần chay = "vegetarian".
- dish_type mapping: dùng dish_type khi user đề cập món cụ thể — "phở" = "phở", "bún chả" = "bún_chả", "cơm" = "cơm", "sushi" = "sushi", "bbq/nướng hàn" = "bbq", "buffet" = "buffet", "fine dining/sang trọng" = "fine_dining", "bình dân/casual" = "casual_dining".
- ambiance mapping: "lãng mạn/hẹn hò" = "romantic", "ít người/yên tĩnh/cozy" = "cozy_indoor", "sang trọng/đẹp" = "elegant", "bình dân" = "casual", "vỉa hè/street food" = "street_food_style".
- amenity mapping: "chỗ để xe/đỗ xe" = "parking", "nhạc sống" = "live_music", "ngoài trời" = "outdoor_seating", "điều hoà" = "air_conditioning".
- Nếu user đề cập "đang mở", "còn mở", "mấy giờ mở", hoặc một giờ cụ thể: BẮT BUỘC gọi check_open_status sau khi tìm được quán.
- Calculate costs accurately for groups.
- If no restaurants match the criteria after searching, use the human_escalation_fallback tool.
- Respond in Vietnamese as the user is asking in Vietnamese.
- Be helpful, accurate, and culturally appropriate.
- After gathering all necessary information, provide the Final Answer immediately without further tool calls.
- QUAN TRỌNG: Nếu câu hỏi KHÔNG liên quan đến nhà hàng hoặc ẩm thực tại Hà Nội (ví dụ: sân bóng, khách sạn, thời tiết, mua sắm, ...), KHÔNG gọi bất kỳ tool nào. Trả lời ngay bằng Final Answer: "Rất tiếc, tôi chỉ hỗ trợ thông tin về các nhà hàng và ẩm thực tại Hà Nội. Bạn có muốn tìm quán ăn không?"
"""

    def run(self, user_input: str) -> str:
        """
        Vòng lặp ReAct cốt lõi.
        Mỗi bước log đầy đủ Thought, Tool Call, Observation qua logger và tracker.
        """
        logger.log_event("AGENT_RUN_START", {"input": user_input, "model": self.llm.model_name})

        history_text = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.history
        ])
        current_prompt = f"{history_text}\nUser Request: {user_input}\n" if self.history else f"User Request: {user_input}\n"
        steps = 0

        while steps < self.max_steps:
            step_num = steps + 1

            # 1. Gọi LLM để sinh ra Thought và Action
            response = self.llm.generate(current_prompt, system_prompt=self.system_prompt)
            tracker.track_request(
                self.llm.provider, self.llm.model_name,
                response["usage"], response["latency_ms"]
            )
            tracker.track_step(step_num, "thought", self.llm.provider, response["latency_ms"])
            content = response["content"]

            # Parse và log Thought
            thought_match = re.search(r'Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)', content, re.DOTALL)
            thought_text = thought_match.group(1).strip() if thought_match else content.strip()
            logger.log_thought(step_num, thought_text)

            # 2. Kiểm tra nếu có Final Answer
            if "Final Answer:" in content:
                answer = content.split("Final Answer:", 1)[1].strip()
                self.history.append({"role": "user", "content": user_input})
                self.history.append({"role": "assistant", "content": answer})
                # Giữ tối đa 10 lượt gần nhất (20 messages) tránh vượt context window
                self.history = self.history[-20:]
                logger.log_agent_finish(step_num, "finish", answer)
                return answer

            # 3. Parse Action và Action Input
            try:
                action_match = re.search(r'Action:\s*(\w+)', content)
                if not action_match:
                    logger.log_event("AGENT_PARSE_ERROR", {"error": "No Action found", "step": step_num})
                    steps += 1
                    continue

                tool_name = action_match.group(1)

                json_match = re.search(r'Action Input:\s*(\{[^{}]*\})', content, re.DOTALL)
                if not json_match:
                    logger.log_event("AGENT_PARSE_ERROR", {"error": "No Action Input JSON found", "step": step_num})
                    steps += 1
                    continue

                action_input_str = json_match.group(1).strip()
                action_input_str = action_input_str.strip('`').strip()
                if action_input_str.startswith('json'):
                    action_input_str = action_input_str[4:].strip()

                action_input = json.loads(action_input_str)

            except Exception as e:
                logger.log_event("AGENT_PARSE_ERROR", {"error": str(e), "step": step_num})
                steps += 1
                continue

            # 4. Thực thi tool và đo latency
            t0 = time.time()
            observation, success = self._execute_tool(tool_name, action_input)
            tool_latency_ms = int((time.time() - t0) * 1000)

            # Log đầy đủ với các method mới
            logger.log_tool_call(step_num, tool_name, action_input, observation)
            logger.log_tool_result(step_num, tool_name, success, observation)
            tracker.track_step(step_num, "tool_call", self.llm.provider, tool_latency_ms)

            # 5. Cập nhật prompt cho vòng lặp tiếp theo
            current_prompt += f"{content}\nObservation: {observation}\n"

            steps += 1

        # Nếu vượt quá max_steps -> Return Fallback
        logger.log_agent_finish(steps, "max_iter", "")
        return "Xin lỗi, tôi đã mất quá nhiều thời gian suy nghĩ mà chưa ra kết quả. Vui lòng thử lại!"

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Thực thi Tool một cách an toàn. Trả về (result, success).
        """
        if tool_name in self.tools:
            try:
                result = self.tools[tool_name](**args)
                return result, True
            except Exception as e:
                logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": str(e)})
                return json.dumps({"error": f"Lỗi khi chạy tool: {str(e)}"}), False

        return json.dumps({"error": f"Tool '{tool_name}' không tồn tại!"}), False
