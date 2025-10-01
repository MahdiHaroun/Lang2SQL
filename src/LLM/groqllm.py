from langchain_groq import ChatGroq
import os 
from dotenv import load_dotenv

class GroqLLM:
    
    @staticmethod
    def get_llm():
        try:
            load_dotenv()
            groq_api_key = os.getenv("GROQ_API_KEY")
            print(groq_api_key)
            os.environ["GROQ_API_KEY"] = groq_api_key
            llm = ChatGroq(api_key=groq_api_key, model="openai/gpt-oss-120b")
            return llm
        except Exception as e:
            raise ValueError(f"Error occurred with exception : {e}")