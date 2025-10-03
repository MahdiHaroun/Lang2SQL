from pydantic import BaseModel, Field  ,  EmailStr
from typing import Optional
from datetime import datetime


class DBConfig(BaseModel):
    owner_id : int = Field(..., description="ID of the user who owns this database connection")
    db_type: str = Field(..., description="Database type, e.g. Postgres/MySQL")
    username: str = Field(..., description="Database username")
    db_password: str = Field(..., description="Database password")
    host: str = Field(..., description="Database host address")
    port: int = Field(..., description="Database port number")
    database_name: str = Field(..., description="Name of the database to connect to")
    

class QueryRequest(BaseModel):
    question: str = Field(..., description="The user's question to be answered using SQL queries")
    thread_id: str = Field(default="default-thread", description="A unique identifier for the conversation thread")




class User_create(BaseModel):
    name : str 
    email : EmailStr
    password : str
    thread_id : str

class User_Response(BaseModel):
    
    name: str 
    email: EmailStr
    thread_id : str
    
    
    class Config:
        from_attributes = True

class User_login(BaseModel):   #used form instead
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None