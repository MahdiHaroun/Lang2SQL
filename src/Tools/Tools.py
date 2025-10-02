from langchain_core.tools import Tool, tool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import MessagesState
from dotenv import load_dotenv
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
    print(f"GROQ_API_KEY found: {bool(os.getenv('GROQ_API_KEY'))}")
    llm = None

from src.Tools_Functions.nlp_gen import nlp_chain 
from src.Tools_Functions.fetch_db import fetch_db 
from src.Tools_Functions.db_connector import DBConnector
from src.Tools_Functions.execute_sql import execute_sql
from src.Tools_Functions.summary import SummaryGenerator
import os

# Initialize with default values from environment (fallback)
nlp_generator = nlp_chain()
default_db_connector = None
try:
    if all([os.getenv("POSTGRES_HOST"), os.getenv("POSTGRES_PORT"), 
            os.getenv("POSTGRES_DB_NAME"), os.getenv("POSTGRES_USERNAME"), 
            os.getenv("POSTGRES_PASSWORD")]):
        default_db_connector = DBConnector(os.getenv("POSTGRES_HOST"), 
                                         int(os.getenv("POSTGRES_PORT")), 
                                         os.getenv("POSTGRES_DB_NAME"), 
                                         os.getenv("POSTGRES_USERNAME"), 
                                         os.getenv("POSTGRES_PASSWORD"))
except Exception as e:
    print(f"Warning: Could not initialize default database connector: {e}")

# Global variables that can be updated
db_connector = default_db_connector
fetch_db_instance = None
execute_sql_instance = None
summary_generator = SummaryGenerator()

# Initialize database tools if connector is available
if db_connector:
    fetch_db_instance = fetch_db(db_connector)  
    execute_sql_instance = execute_sql(db_connector)

def update_db_connector(new_db_connector):
    """Update the global database connector and reinitialize tools"""
    global db_connector, fetch_db_instance, execute_sql_instance
    
    db_connector = new_db_connector
    fetch_db_instance = fetch_db(db_connector)
    execute_sql_instance = execute_sql(db_connector)
    print(f"Database connector updated successfully")


@tool
def fetch_db_schema() -> str:
    """Fetches the database schema and returns it as a string."""
    try:
        if not db_connector:
            raise ValueError("Database connection not configured. Please connect to a database first.")
        
        print("Fetching the database schema...")
        connector = db_connector.get_connection_string()
        if connector is None:
            raise ValueError("Database connection failed.")
        print("Database connected successfully.")
        
        if not fetch_db_instance:
            raise ValueError("Database fetch tool not initialized.")
        
        db_schema = fetch_db_instance.get_db_schema()
        print("Database schema fetched successfully.")
        return str(db_schema)
    except Exception as e: 
        raise ValueError(f"Error occurred with exception : {e}")


@tool
def generate_sql(question: str) -> str:
    """Generates an SQL query based on the user's question. This tool fetches the database schema internally."""
    try:
        if not db_connector or not fetch_db_instance:
            raise ValueError("Database connection not configured. Please connect to a database first.")
            
        print("Fetching schema for SQL generation...")
        # Get fresh schema for SQL generation
        db_schema = fetch_db_instance.get_db_schema()
        print("Generating SQL query for Read operation...")
        sql_chain = nlp_generator.get_sql_chain()
        generated_sql = sql_chain.invoke({"question": question, "db_schema": db_schema})
        print(f"Generated SQL: {generated_sql}")
        return str(generated_sql)
    except Exception as e:
        raise ValueError(f"Error occurred with exception : {e}")
        
        
@tool        
def execute_sql_query(query: str) -> str:
    """Executes the generated SQL query and returns the query results."""
    try:
        if not db_connector or not execute_sql_instance:
            raise ValueError("Database connection not configured. Please connect to a database first.")
            
        result = execute_sql_instance.execute_query(query)
        print(f"Query Result: {result}")
        return str(result)
    except Exception as e: 
        raise ValueError(f"Error occurred with exception : {e}")
        

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
    


    