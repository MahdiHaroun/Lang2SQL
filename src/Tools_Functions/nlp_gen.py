
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
                 "IMPORTANT RULES: "
                 "1. Return ONLY the SQL query without any markdown formatting, explanations, or code blocks. "
                 "2. Do not include ```sql or ``` markers. "
                 "3. ALWAYS use the existing schemas and tables from the provided schema. "
                 "4. If creating new tables, use the 'mahdi_schema' schema, NOT the 'public' schema. "
                 "5. For table operations, always prefix table names with the schema (e.g., mahdi_schema.table_name). "
                 "6. Only work with the tables and columns that exist in the provided schema. "
                 "Database Schema: {db_schema}"),
                ("human", "Question: {question}")
            ])
        
            sql_chain = prompt | self.llm | StrOutputParser() 

            return sql_chain
    
        except Exception as e: 
            raise ValueError(f"Error occurred with exception : {e}")
