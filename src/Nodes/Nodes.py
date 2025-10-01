import re
from typing import Dict, Any, List
from src.State.GraphState import GraphState
from src.Tools.nlp_gen import nlp_chain
from src.Tools.fetch_db import fetch_db
from src.Tools.db_connector import DBConnector
from src.Tools.execute_sql import execute_sql
from src.Tools.summary import SummaryGenerator
from langchain_core.tools import Tool

        
nlp_generator = nlp_chain()
db_connector = DBConnector("localhost", 5432, "sqlagentwsl" , "mahdi" , "0816")
fetch_db = fetch_db(db_connector)  
execute_sql = execute_sql(db_connector)
summary_generator = SummaryGenerator()


def fetch_db_schema(state:GraphState) -> GraphState:
        try : 
            print("Fetching the database schema...")
            connecter = db_connector.get_connection_string()
            if connecter is None:
                raise ValueError("Database connection failed.")
            print("Database connected successfully.")
            db_schema = fetch_db.get_db_schema()
            state["db_schema"] = db_schema
            print("Database schema fetched successfully.")
            return state
        except Exception as e: 
            raise ValueError(f"Error occurred with exception : {e}")
            
          
        

def generate_sql( state: GraphState) -> GraphState:
        try : 
            print("Generating SQL query for Read operation...")
            
            # Use .get() for safer key access
            question = state.get("question", "")
            db_schema = state.get("db_schema", {})
            
            if not question:
                raise ValueError("Missing or empty 'question' in state")
            if not db_schema:
                raise ValueError("Missing or empty 'db_schema' in state")
            
            print(f"Question: {question}")
            print(f"DB Schema available: {bool(db_schema)}")

            sql_chain = nlp_generator.get_sql_chain()
            generated_sql = sql_chain.invoke({"question": question, "db_schema": db_schema})
            state["generated_sql"] = generated_sql
            print(f"Generated SQL: {generated_sql}")
            print(f"State keys after SQL generation: {list(state.keys())}")
            print(f"Generated SQL is set: {'generated_sql' in state}")
            return state
        except Exception as e: 
            raise ValueError(f"Error occurred with exception : {e}")
        

def execute_sql_query(state:GraphState) -> GraphState:
        try : 
            print("Executing SQL query...")
            print(f"State keys received: {list(state.keys())}")
            print(f"State content: {state}")
            
            # Use .get() for safer key access
            raw_query = state.get("generated_sql", "")
            
            if not raw_query:
                raise ValueError("Missing or empty 'generated_sql' in state")
            
            # Clean the SQL query by removing markdown formatting
            query = _clean_sql_query(raw_query)
            
            print(f"Raw query: {raw_query}")
            print(f"Cleaned query: {query}")
            result = execute_sql.execute_query(query)
            state["query_result"] = result
            print(f"Query Result: {result}")
            return state
        except Exception as e: 
            raise ValueError(f"Error occurred with exception : {e}")
        


def get_summary(state:GraphState) -> GraphState: 
        try : 
            print("Generating summary of the SQL query result...")
            
            # Use .get() for safer key access
            question = state.get("question", "")
            query_result = state.get("query_result", "No results available.")
            
            if not question:
                raise ValueError("Missing or empty 'question' in state")
            
            print(f"Question: {question}")
            print(f"Query result type: {type(query_result)}")
            
            summary = summary_generator.generate_summary(question, query_result)
            state["summary"] = summary
            print(f"Summary: {summary}")
            return state
        except Exception as e:  
            raise ValueError(f"Error occurred with exception : {e}")
        

     
     
        

    

        
    
            
fetch_db_schema_tool = Tool.from_function(
    fetch_db_schema,  
    name="fetch_db_schema",
    description="Fetches the database schema and updates the state with the schema information. Call this first before any SQL operations."
)
generate_sql_tool = Tool.from_function(
    generate_sql,  
    name="generate_sql",
    description="Generates an SQL query based on the user's question and the database schema. Call after fetching the schema."
)
execute_sql_query_tool = Tool.from_function(
    execute_sql_query,  
    name="execute_sql_query",
    description="Executes the generated SQL query and updates the state with the query results. Call after generating SQL."
)
get_summary_tool = Tool.from_function(
    get_summary,  
    name="get_summary",
    description="Generates a summary of the SQL query results based on the user's original question. Call after executing the query."
)


from src.LLM.groqllm import GroqLLM
class LLM_withTools:
    def __init__(self):
        self.llm = GroqLLM.get_llm()
        self.tools = [fetch_db_schema_tool, generate_sql_tool, execute_sql_query_tool, get_summary_tool]

    def get_llm_with_tools(self):
         llm_with_tools = self.llm.bind_tools(self.tools)
         return llm_with_tools
    

assistant_system_message = """
You are an expert SQL agent designed to assist users with database-related queries.
Your primary functions include:
1. Understanding user questions and generating appropriate SQL queries.
2. Executing SQL queries against a PostgreSQL database.
3. Summarizing the results of SQL queries in a user-friendly manner.
You will utilize a set of specialized tools to accomplish these tasks:
- fetch_db_schema: Fetches the database schema and updates the state with the schema information. No input required.
- generate_sql: Generates an SQL query based on the user's question and the database schema. Requires 'question' and 'db_schema' in the state.
- execute_sql_query: Executes the generated SQL query and updates the state with the query results. Requires 'generated_sql' in the state.
- get_summary: Generates a summary of the SQL query results based on the user's original question. Requires 'question' and 'query_result' in the state.
Your responses should be concise and focused on the task at hand. Always ensure that the SQL queries you generate are syntactically correct and optimized for performance.
you must follow these guidelines:
-always fetch the database schema first and understand it before generating any SQL queries.
-ensure that the SQL queries you generate are syntactically correct and optimized for performance.
-when summarizing results, focus on the key insights and avoid unnecessary technical jargon.
"""

def _clean_sql_query(query: str) -> str:
    """Clean SQL query by removing markdown formatting and extra whitespace."""
    # Remove markdown code block markers (case insensitive)
    query = re.sub(r'```sql\n?', '', query, flags=re.IGNORECASE)
    query = re.sub(r'```\n?', '', query)
    
    # Remove any leading/trailing whitespace and normalize internal whitespace
    query = re.sub(r'\s+', ' ', query.strip())
    
    # Ensure query ends with semicolon if it doesn't already
    if query and not query.endswith(';'):
        query += ';'
        
    return query

def agent(state: GraphState):
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        llm_with_tools = LLM_withTools().get_llm_with_tools()
        print("Starting the agent with the provided state...")
        print(f"Initial state: {state}")
        
        # Create messages for the LLM
        messages = [
            SystemMessage(content=assistant_system_message),
            HumanMessage(content=state.get("question", ""))
        ]
        
        result = llm_with_tools.invoke(messages)
        print("Agent completed successfully.")
        print(f"Result: {result}")
        
        # Return the result in a format compatible with the graph
        return {"messages": [result]}
    except Exception as e:  
        raise ValueError(f"Error occurred with exception : {e}")
    


        
