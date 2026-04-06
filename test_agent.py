import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.core.openai_provider import OpenAIProvider

def test_agent():
    load_dotenv()
    
    # Use OpenAI provider
    provider = OpenAIProvider()
    agent = ReActAgent(llm=provider, max_steps=5)
    
    while True:
        user_input = input("Nhập câu hỏi của bạn (hoặc 'quit' để thoát): ")
        if user_input.lower() == 'quit':
            break
        
        print(f"Query: {user_input}")
        print("Agent thinking...")
        
        try:
            response = agent.run(user_input)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_agent()