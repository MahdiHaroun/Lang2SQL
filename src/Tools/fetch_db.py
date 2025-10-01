from typing import Dict, Any
from sqlalchemy import create_engine, text
from src.Tools.db_connector import DBConnector


class fetch_db: 
    def __init__(self, db_connector: DBConnector):
        self.connection_string = db_connector.get_connection_string()
        # Use synchronous connection for PostgreSQL
        sync_connection_string = self.connection_string.replace("postgresql+asyncpg://", "postgresql://")
        self.engine = create_engine(sync_connection_string)

    def get_db_schema(self) -> Dict[str, Any]: 
        try : 
            with self.engine.connect() as connection : 
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
        except Exception as e: 
            raise ValueError(f"Error occurred with exception : {e}")




