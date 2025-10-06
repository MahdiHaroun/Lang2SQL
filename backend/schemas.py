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
    user_id: int = Field(..., description="ID of the user making the request")
    session_id: str = Field(..., description="Session ID (UUID) that serves as thread_id")
    question: str = Field(..., description="The user's question to be answered using SQL queries")
    




class User_create(BaseModel):
    name : str 
    email : EmailStr
    password : str
    

class User_Response(BaseModel):
    
    name: str 
    email: EmailStr
    
    
    
    class Config:
        from_attributes = True

class User_login(BaseModel):   #used form instead
    email: EmailStr
    password: str

class Token(User_Response):
    
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None
    
    



class Session(BaseModel):
    session_token: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


