from pydantic import BaseModel, Field 



class DBConfig(BaseModel):
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    host: str = Field(..., description="Database host address")
    port: int = Field(..., description="Database port number")
    database: str = Field(..., description="Name of the database to connect to")
    

class QueryRequest(BaseModel):
    question: str = Field(..., description="The user's question to be answered using SQL queries")
    thread_id: str = Field(default="default-thread", description="A unique identifier for the conversation thread")