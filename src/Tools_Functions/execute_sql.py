from typing import List, Any, Union, Dict
from src.Tools_Functions.db_connector import DBConnector
from sqlalchemy import create_engine, text


class execute_sql: 
    def __init__(self, db_connector: DBConnector): 
        self.db_connector = db_connector

    def execute_query(self, query: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]: 
        """Execute SQL query and return results"""
        try:
            connection = self.db_connector.connect()
            try:
                # Use begin() for auto-commit transactions
                with connection.begin() as trans:
                    result = connection.execute(text(query))
                    
                    # Check if the query returns rows (SELECT queries)
                    if result.returns_rows:
                        rows = result.fetchall()
                        # Convert rows to list of dictionaries for easier handling
                        if rows:
                            columns = result.keys()
                            return [dict(zip(columns, row)) for row in rows]
                        else:
                            return []
                    else:
                        # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                        # Transaction will be automatically committed when exiting the context
                        return {"affected_rows": result.rowcount, "message": "Query executed successfully"}
            finally:
                connection.close()
                    
        except Exception as e:  
            raise ValueError(f"Error occurred with exception: {e}")
            