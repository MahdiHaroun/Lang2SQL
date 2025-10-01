
from langchain_core.output_parsers import StrOutputParser
from src.LLM.groqllm import GroqLLM

class nlp_chain: 
    def __init__(self):
        self.llm = GroqLLM.get_llm()
        

    def get_sql_chain(self ):

        try : 

            from langchain.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful AI assistant that generates SQL queries. "
                 "Use the provided database schema and question to generate a valid SQL query. "
                 "IMPORTANT: Return ONLY the SQL query without any markdown formatting, explanations, or code blocks. "
                 "Do not include ```sql or ``` markers. "
                 "Make sure to only generate SQL queries that are compatible with the provided schema. "
                 "Database Schema: {db_schema}"),
                ("human", "Question: {question}")
            ])
        
            sql_chain = prompt | self.llm | StrOutputParser() 

            return sql_chain
    
        except Exception as e: 
            raise ValueError(f"Error occurred with exception : {e}")
