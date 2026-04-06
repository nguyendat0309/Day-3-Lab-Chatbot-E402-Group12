from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("API_KEY"))

def PromtForAgent(data):
    maxtime = 3
    start = 0
    final = ""
    context = []
    while start < 3:
        full_prompt = f"""
            Bạn là một trợ lý AI chuyên nghiệp. Hãy mô tả tóm tắt tài liệu dưới đây một cách thật đầy đủ, ngắn gọn.
            Lưu ý: 
            - Nếu dữ liệu bị null hãy nói "tôi không tìm thấy dữ liệu"
            - nếu context rỗng thì bỏ qua, nếu không rỗng thì đọc kĩ và sử dụng
            câu: {data}
            context: {context}
            """

        response = client.responses.create(
            model=os.getenv("MODEL_TALK"),
            input=full_prompt,
        )

        out = response.output_text
        if start == 2:
            final = out
        context.append(out)
        start = start + 1

    return final