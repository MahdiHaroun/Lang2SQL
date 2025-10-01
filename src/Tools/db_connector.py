
class DBConnector:
    def __init__(self , host:str , port:int , database:str , user:str , password:str): 
        self.connection_string = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

    def get_connection_string(self) -> str:
        return self.connection_string