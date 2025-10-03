from typing import Dict, Any
from sqlalchemy import create_engine, text
from src.Tools_Functions.db_connector import DBConnector


class fetch_db: 
    def __init__(self, db_connector: DBConnector):
        self.db_connector = db_connector

    def get_db_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            connection = self.db_connector.connect()
            try:
                overview = {}
                result = connection.execute(text("""
                    SELECT table_schema, table_name, column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY table_schema, table_name, ordinal_position;
                """))

                for r in result:
                    schema = r[0]  # table_schema
                    table = r[1]   # table_name
                    col = r[2]     # column_name
                    dtype = r[3]   # data_type

                    overview.setdefault(schema, {})
                    overview[schema].setdefault(table, [])
                    overview[schema][table].append({"column": col, "type": dtype})

                return overview
            finally:
                connection.close()
        except Exception as e: 
            raise ValueError(f"Error occurred with exception: {e}")




