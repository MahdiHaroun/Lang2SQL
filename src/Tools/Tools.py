from langchain_core.tools import Tool, tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import MessagesState
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

# Load environment variables - try multiple paths
env_paths = [
    os.path.join(os.path.dirname(__file__), "../../.env"),  # From Tools directory
    os.path.join(os.getcwd(), ".env"),  # From current working directory
    ".env"  # Relative to current directory
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

# Initialize ChatGroq with error handling
try:
    llm = ChatGroq(model="openai/gpt-oss-120b")
except Exception as e:
    print(f"Warning: Failed to initialize ChatGroq: {e}")
   
    llm = None

from src.Tools_Functions.nlp_gen import nlp_chain 
from src.Tools_Functions.fetch_db import fetch_db 
from src.Tools_Functions.db_connector import DBConnector
from src.Tools_Functions.execute_sql import execute_sql
from src.Tools_Functions.summary import SummaryGenerator
import os

# Initialize tools - database connection will be set via /connect_db endpoint
nlp_generator = nlp_chain()

# Global variables that will be updated when database is connected via FastAPI
db_connector = None
fetch_db_instance = None
execute_sql_instance = None
summary_generator = SummaryGenerator()

def update_db_connector(connection_string: str):
    """Update the global database connector with a new connection string and reinitialize tools"""
    global db_connector, fetch_db_instance, execute_sql_instance
    
    try:
        db_connector = DBConnector(connection_string)
        fetch_db_instance = fetch_db(db_connector)
        execute_sql_instance = execute_sql(db_connector)
        print(f"Database connector updated successfully")
        return True
    except Exception as e:
        print(f"Failed to update database connector: {e}")
        return False

def is_database_connected():
    """Check if database is connected and tools are initialized"""
    return db_connector is not None and fetch_db_instance is not None and execute_sql_instance is not None


@tool
def fetch_db_schema() -> str:
    """Fetches the database schema and returns it as a string."""
    try:
        if not is_database_connected():
            return "Database not connected. Please use the /connect_db/{db_id} endpoint to establish a database connection first."
        
        print("Fetching the database schema...")
        db_schema = fetch_db_instance.get_db_schema()
        print("Database schema fetched successfully.")
        return str(db_schema)
    except Exception as e: 
        raise ValueError(f"Error occurred with exception: {e}")

@tool
def generate_sql(question: str) -> str:
    """Generates an SQL query based on the user's question. This tool fetches the database schema internally."""
    try:
        if not is_database_connected():
            raise ValueError("Database not connected. Please use the /connect_db/{db_id} endpoint to establish a database connection first.")
            
        print("Fetching schema for SQL generation...")
        # Get fresh schema for SQL generation
        db_schema = fetch_db_instance.get_db_schema()
        print("Generating SQL query for Read operation...")
        sql_chain = nlp_generator.get_sql_chain()
        generated_sql = sql_chain.invoke({"question": question, "db_schema": db_schema})
        print(f"Generated SQL: {generated_sql}")
        return str(generated_sql)
    except Exception as e:
        raise ValueError(f"Error occurred with exception: {e}")
        
        
@tool        
def execute_sql_query(query: str) -> str:
    """Executes the generated SQL query and returns the query results."""
    try:
        if not is_database_connected():
            raise ValueError("Database not connected. Please use the /connect_db/{db_id} endpoint to establish a database connection first.")
            
        result = execute_sql_instance.execute_query(query)
        print(f"Query Result: {result}")
        return str(result)
    except Exception as e: 
        raise ValueError(f"Error occurred with exception: {e}")
        

@tool
def get_summary(question_and_result: str) -> str:
    """Generates a summary of SQL query results. Input should be formatted as 'QUESTION: <question> RESULT: <result>'"""
    try:
        print("Generating summary of the SQL query result...")
        # Parse the combined input
        parts = question_and_result.split("RESULT:")
        if len(parts) != 2:
            return "Error: Please format input as 'QUESTION: <question> RESULT: <result>'"
        
        question = parts[0].replace("QUESTION:", "").strip()
        result = parts[1].strip()
        
        summary = summary_generator.generate_summary(question, result)
        return str(summary)
    except Exception as e:
        raise ValueError(f"Error occurred with exception : {e}")
    


    