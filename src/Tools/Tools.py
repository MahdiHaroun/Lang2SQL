from langchain_core.tools import Tool, tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import MessagesState
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os
import time 



from src.Tools_Functions.nlp_gen import nlp_chain 
from src.Tools_Functions.fetch_db import fetch_db 
from src.Tools_Functions.db_connector import DBConnector
from src.Tools_Functions.execute_sql import execute_sql
from src.Tools_Functions.summary import SummaryGenerator


# Load environment variables - try multiple paths
env_paths = [
    os.path.join(os.path.dirname(__file__), "../../.env"),  
    os.path.join(os.getcwd(), ".env"),  
    ".env"  
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

#LLM

try:
    llm = ChatGroq(model="openai/gpt-oss-120b")
except Exception as e:
    print(f"Warning: Failed to initialize ChatGroq: {e}")
   
    llm = None



# Initialize tools - database connection will be set via /connect_db endpoint
nlp_generator = nlp_chain()
summary_generator = SummaryGenerator()

session_connectors = {}

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from src.redis_client import redis_client




def update_db_connector(connection_string: str, session_id: str = "default"):
    """Update the database connector for a specific session"""
    
    
    try:
        session_data = {
            "connection_string": connection_string,
            "created_at": str(int(time.time())),
            "status": "connected"
        }  
        print("-----Storing Session Data in Redis-----")
        for key, value in session_data.items():
            redis_client.hset(f"session:{session_id}", key, value)  

        redis_client.expire(f"session:{session_id}", 86400)


        try:
            print("-----Storing DB Schema in Redis-----")
            connector = DBConnector(connection_string)
            fetch_db_instance = fetch_db(connector)
            db_schema = fetch_db_instance.get_db_schema()
            redis_client.hset(f"session:{session_id}", "db_schema", db_schema)
            
            print(f"Database connector updated successfully for session: {session_id}")
            return True
        except Exception as schema_error:
            print(f"Connection successful but schema caching failed for session {session_id}: {schema_error}")
            return True  
            
    except Exception as e:
        print(f"Failed to update database connector for session {session_id}: {e}")
        return False       




def is_database_connected(session_id: str = "default"):
    """Check if a session exists in Redis and is valid"""
    try:
        if not redis_client.is_connected():
            print(f"Redis not connected when checking session {session_id}")
            return False
        
        # Check if session exists and has connection string
        connection_string = redis_client.hget(f"session:{session_id}", "connection_string")
        return connection_string is not None
    except Exception as e:
        print(f"Error checking session {session_id}: {e}")
        return False




def get_session_tools(session_id: str = "default"):
    """Retrieve DB tools for a session from Redis with caching"""
    if not is_database_connected(session_id):
        return None, None, None
    
    try:
        # Check if we already have a connector cached
        if session_id in session_connectors:
            connector = session_connectors[session_id]
            fetch_db_instance = fetch_db(connector)
            execute_sql_instance = execute_sql(connector)
            return connector, fetch_db_instance, execute_sql_instance
        
        # Create new connector only if not cached
        connection_string = redis_client.hget(f"session:{session_id}", "connection_string")
        if not connection_string:
            return None, None, None
            
        connector = DBConnector(connection_string)
        session_connectors[session_id] = connector  # Cache it
        
        fetch_db_instance = fetch_db(connector)
        execute_sql_instance = execute_sql(connector)
        
        return connector, fetch_db_instance, execute_sql_instance
    except Exception as e:
        print(f"Error getting session tools for {session_id}: {e}")
        return None, None, None
    


def cleanup_session(session_id: str):
    """Clean up session data from Redis and memory"""
    try:
        # Clean up Redis data
        redis_client.delete(f"session:{session_id}")
        
        # Clean up memory cache
        if session_id in session_connectors:
            del session_connectors[session_id]
        
        return True
    except Exception as e:
        print(f"Error cleaning up session {session_id}: {e}")
        return False
    

def get_session_info(session_id: str):
    """Get session information from Redis"""
    try:
        if not is_database_connected(session_id):
            return None
        
        session_data = {}
        keys = ["connection_string", "created_at", "status", "db_schema"]
        for key in keys:
            value = redis_client.hget(f"session:{session_id}", key)
            if value:
                session_data[key] = value
        
        return session_data if session_data else None
    except Exception as e:
        print(f"Error getting session info for {session_id}: {e}")
        return None



def create_session_tools(session_id: str):
    
    @tool
    def fetch_db_schema() -> str:
        """Fetch database schema for a session"""
        try:
            if not is_database_connected(session_id):
                return f"Database not connected for session {session_id}."
            
            _, fetch_db_instance, _ = get_session_tools(session_id)
            db_schema = fetch_db_instance.get_db_schema()
            # Update Redis schema cache
            redis_client.hset(f"session:{session_id}", "db_schema", db_schema)
            return str(db_schema)
        except Exception as e: 
            raise ValueError(f"Error: {e}")

    @tool
    def generate_sql(question: str) -> str:
        """Generate SQL query using session-specific schema"""
        try:
            if not is_database_connected(session_id):
                raise ValueError(f"Database not connected for session {session_id}.")
            
            # Get cached schema from Redis
            db_schema = redis_client.hget(f"session:{session_id}", "db_schema")
            if not db_schema:
                _, fetch_db_instance, _ = get_session_tools(session_id)
                db_schema = fetch_db_instance.get_db_schema()
                redis_client.hset(f"session:{session_id}", "db_schema", db_schema)

            sql_chain = nlp_generator.get_sql_chain()
            generated_sql = sql_chain.invoke({"question": question, "db_schema": db_schema})
            return str(generated_sql)
        except Exception as e:
            raise ValueError(f"Error: {e}")

    @tool
    def execute_sql_query(query: str) -> str:
        """Execute SQL query for a session"""
        try:
            if not is_database_connected(session_id):
                raise ValueError(f"Database not connected for session {session_id}.")
            
            _, _, execute_sql_instance = get_session_tools(session_id)
            result = execute_sql_instance.execute_query(query)
            return str(result)
        except Exception as e: 
            raise ValueError(f"Error: {e}")
    
    return [fetch_db_schema, generate_sql, execute_sql_query]

# Default tools for backward compatibility before session management


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
 


    