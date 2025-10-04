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

# Session-based database connectors
session_db_connectors = {}
session_fetch_db = {}
session_execute_sql = {}
summary_generator = SummaryGenerator()

def update_db_connector(connection_string: str, session_id: str = "default"):
    """Update the database connector for a specific session"""
    global session_db_connectors, session_fetch_db, session_execute_sql
    
    try:
        session_db_connectors[session_id] = DBConnector(connection_string)
        session_fetch_db[session_id] = fetch_db(session_db_connectors[session_id])
        session_execute_sql[session_id] = execute_sql(session_db_connectors[session_id])
        print(f"Database connector updated successfully for session: {session_id}")
        return True
    except Exception as e:
        print(f"Failed to update database connector for session {session_id}: {e}")
        return False

def is_database_connected(session_id: str = "default"):
    """Check if database is connected for a specific session"""
    return (session_id in session_db_connectors and 
            session_id in session_fetch_db and 
            session_id in session_execute_sql)

def get_session_tools(session_id: str):
    """Get database tools for a specific session"""
    if not is_database_connected(session_id):
        return None, None, None
    return (session_db_connectors.get(session_id), 
            session_fetch_db.get(session_id), 
            session_execute_sql.get(session_id))


def create_session_tools(session_id: str):
    """Create session-specific tools"""
    
    @tool
    def fetch_db_schema() -> str:
        """Fetches the database schema and returns it as a string."""
        try:
            if not is_database_connected(session_id):
                return f"Database not connected for session {session_id}. Please use the /connect_db/{{db_id}} endpoint to establish a database connection first."
            
            print(f"Fetching the database schema for session {session_id}...")
            _, fetch_db_instance, _ = get_session_tools(session_id)
            db_schema = fetch_db_instance.get_db_schema()
            print("Database schema fetched successfully.")
            return str(db_schema)
        except Exception as e: 
            raise ValueError(f"Error occurred with exception: {e}")

    @tool
    def generate_sql(question: str) -> str:
        """Generates an SQL query based on the user's question. This tool fetches the database schema internally."""
        try:
            if not is_database_connected(session_id):
                raise ValueError(f"Database not connected for session {session_id}. Please use the /connect_db/{{db_id}} endpoint to establish a database connection first.")
                
            print(f"Fetching schema for SQL generation for session {session_id}...")
            # Get fresh schema for SQL generation
            _, fetch_db_instance, _ = get_session_tools(session_id)
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
            if not is_database_connected(session_id):
                raise ValueError(f"Database not connected for session {session_id}. Please use the /connect_db/{{db_id}} endpoint to establish a database connection first.")
                
            _, _, execute_sql_instance = get_session_tools(session_id)
            result = execute_sql_instance.execute_query(query)
            print(f"Query Result: {result}")
            return str(result)
        except Exception as e: 
            raise ValueError(f"Error occurred with exception: {e}")
    
    return [fetch_db_schema, generate_sql, execute_sql_query]

# Default tools for backward compatibility
@tool
def fetch_db_schema() -> str:
    """Fetches the database schema and returns it as a string."""
    session_id = "default"
    try:
        if not is_database_connected(session_id):
            return "Database not connected. Please use the /connect_db/{db_id} endpoint to establish a database connection first."
        
        print("Fetching the database schema...")
        _, fetch_db_instance, _ = get_session_tools(session_id)
        db_schema = fetch_db_instance.get_db_schema()
        print("Database schema fetched successfully.")
        return str(db_schema)
    except Exception as e: 
        raise ValueError(f"Error occurred with exception: {e}")

@tool
def generate_sql(question: str) -> str:
    """Generates an SQL query based on the user's question. This tool fetches the database schema internally."""
    session_id = "default"
    try:
        if not is_database_connected(session_id):
            raise ValueError("Database not connected. Please use the /connect_db/{db_id} endpoint to establish a database connection first.")
            
        print("Fetching schema for SQL generation...")
        _, fetch_db_instance, _ = get_session_tools(session_id)
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
    session_id = "default"
    try:
        if not is_database_connected(session_id):
            raise ValueError("Database not connected. Please use the /connect_db/{db_id} endpoint to establish a database connection first.")
            
        _, _, execute_sql_instance = get_session_tools(session_id)
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
    


    