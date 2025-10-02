from langchain_groq import ChatGroq 
from src.Tools.Tools import fetch_db_schema , generate_sql , execute_sql_query  ,get_summary
from dotenv import load_dotenv
load_dotenv("../../.env")


class llm_with_tools: 
    def __init__(self ): 
        self.llm = ChatGroq(model= "openai/gpt-oss-120b")
        self.tool_box = [fetch_db_schema , generate_sql , execute_sql_query , get_summary]


    def llm_with_tools (self): 
        llm_with_tool =  self.llm.bind_tools(self.tool_box)
        return llm_with_tool
    
    def get_tools(self):
        return self.tool_box
    

    