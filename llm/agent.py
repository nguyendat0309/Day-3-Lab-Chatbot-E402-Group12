from openai import OpenAI
import os
import re, json
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("API_KEY"))
class chatBotAgent():
    def __init__(self, searchP, searchD, sentence, data, promtForAgent):
        self.searchP = searchP
        self.searchD = searchD
        self.sentence = sentence
        self.data = data
        self.promtForAgent = promtForAgent

    def reasoning(self):
        full_prompt = f"""
            Bạn là trợ lý AI, Nếu người dùng hỏi về giá cả bạn hãy trích xuất thông tin giá tiền bé nhất và giá tiền lớn nhất
            và trả theo định dạng json: {{"min_price": số, "max_price": số}}. 
            Nếu người dùng hỏi về địa điểm hãy trích xuất thông tin về địa điểm theo dạng json: {{"area": "vùng"}}.
            câu: {self.sentence}
            """

        response = client.responses.create(
            model=os.getenv("MODEL_TALK"),
            input=full_prompt
        )
        res = response.output_text
        match = re.search(r"\{.*\}", res, re.DOTALL)
        js = ""
        if match:
            js = json.loads(match.group())

        if len(js) >= 2:
            res = self.searchP(self.data, js['min_price'], js['max_price'])
            res = self.promtForAgent(res)
        else:
            res = self.searchD(self.data, js['area'])
            res = self.promtForAgent(res)
        return res



