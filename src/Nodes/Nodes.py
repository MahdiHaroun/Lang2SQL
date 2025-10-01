import re
from typing import Dict, Any, List
from src.State.GraphState import GraphState
from src.Tools.nlp_gen import nlp_chain
from src.Tools.fetch_db import fetch_db
from src.Tools.db_connector import DBConnector
from src.Tools.execute_sql import execute_sql
from src.Tools.summary import SummaryGenerator


class AgentNodes():

    def __init__(self):
        
        self.nlp_generator = nlp_chain()
        self.db_connector = DBConnector("localhost", 5432, "sqlagentwsl" , "mahdi" , "0816")
        self.fetch_db = fetch_db(self.db_connector)  
        self.execute_sql = execute_sql(self.db_connector)
        self.summary_generator = SummaryGenerator()

    def _clean_sql_query(self, query: str) -> str:
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

    def fetch_db_schema(self , state:GraphState) -> GraphState:
        try : 
            print("Fetching the database schema...")
            connecter = self.db_connector.get_connection_string()
            if connecter is None:
                raise ValueError("Database connection failed.")
            print("Database connected successfully.")
            db_schema =  self.fetch_db.get_db_schema()
            state["db_schema"] = db_schema
            print("Database schema fetched successfully.")
            return state
        except Exception as e: 
            raise ValueError(f"Error occurred with exception : {e}")
            
          
        

    def generate_sql(self , state: GraphState) -> GraphState:
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

            sql_chain = self.nlp_generator.get_sql_chain()
            generated_sql = sql_chain.invoke({"question": question, "db_schema": db_schema})
            state["generated_sql"] = generated_sql
            print(f"Generated SQL: {generated_sql}")
            print(f"State keys after SQL generation: {list(state.keys())}")
            print(f"Generated SQL is set: {'generated_sql' in state}")
            return state
        except Exception as e: 
            raise ValueError(f"Error occurred with exception : {e}")
        

    def execute_sql_query(self , state:GraphState) -> GraphState:
        try : 
            print("Executing SQL query...")
            print(f"State keys received: {list(state.keys())}")
            print(f"State content: {state}")
            
            # Use .get() for safer key access
            raw_query = state.get("generated_sql", "")
            
            if not raw_query:
                raise ValueError("Missing or empty 'generated_sql' in state")
            
            # Clean the SQL query by removing markdown formatting
            query = self._clean_sql_query(raw_query)
            
            print(f"Raw query: {raw_query}")
            print(f"Cleaned query: {query}")
            result = self.execute_sql.execute_query(query)
            state["query_result"] = result
            print(f"Query Result: {result}")
            return state
        except Exception as e: 
            raise ValueError(f"Error occurred with exception : {e}")
        


    def get_summary(self , state:GraphState) -> GraphState: 
        try : 
            print("Generating summary of the SQL query result...")
            
            # Use .get() for safer key access
            question = state.get("question", "")
            query_result = state.get("query_result", "No results available.")
            
            if not question:
                raise ValueError("Missing or empty 'question' in state")
            
            print(f"Question: {question}")
            print(f"Query result type: {type(query_result)}")
            
            summary = self.summary_generator.generate_summary(question, query_result)
            state["summary"] = summary
            print(f"Summary: {summary}")
            return state
        except Exception as e:  
            raise ValueError(f"Error occurred with exception : {e}")
        

    

        
    
            

    




        
