from typing import List, Any, Union, Dict
from langchain_core.output_parsers import StrOutputParser
from src.LLM.groqllm import GroqLLM


class SummaryGenerator:
    def __init__(self): 
        self.llm = GroqLLM.get_llm()


    def generate_summary(self, question: str, query_result: Union[List[Dict[str, Any]], Dict[str, Any]]) -> str:

        try : 
            from langchain.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert SQL assistant. Provide a concise summary of the SQL query results."),
                ("user", "Given the question: {question} and the SQL query result: {query_result}, provide a brief summary.")
            ])

            summary_chain = prompt | self.llm | StrOutputParser()
            result = summary_chain.invoke({"question": question, "query_result": query_result})

            return result
        
        except Exception as e:  
            raise ValueError(f"Error occurred with exception : {e}")
    