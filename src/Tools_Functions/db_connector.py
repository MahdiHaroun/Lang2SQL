from dotenv import load_dotenv
from sqlalchemy import create_engine, text  

class DBConnector:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = None

    def connect(self):
        """Create and return a database connection"""
        try:
            if not self.engine:
                self.engine = create_engine(self.connection_string)
            connection = self.engine.connect()
            return connection
        except Exception as e:
            raise ValueError(f"Failed to connect to database: {e}")
    
    def get_connection_string(self):
        """Return the connection string"""
        return self.connection_string
