from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("API_KEY"))

def chatbot(data, question):
    full_prompt = f"""
    Bạn là một trợ lý AI chuyên nghiệp. Hãy trả lời câu hỏi một cách rõ ràng dựa vào tài liệu sau: {data}
    - chi tiết và dễ hiểu
    - Nếu không biết hoặc câu hỏi bên ngoài tài liệu, hãy trả lời "Không có dữ liệu".
    - Giữ nội dung ngắn gọn nhưng đầy đủ.
    - cuối cùng là phải định dạng đẹp, dễ nhìn.

    câu hỏi: {question}
    """

    response = client.responses.create(
        model=os.getenv("MODEL_TALK"),
        input=full_prompt
    )
    return response.output_text