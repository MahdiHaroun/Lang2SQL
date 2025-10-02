from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    userdatabase_host: str
    userdatabase_port: int
    userdatabase_password: str
    userdatabase_db_name: str
    userdatabase_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    
    # Optional fields for compatibility
    groq_api_key: Optional[str] = None
    langsmith_tracing: Optional[str] = None
    langsmith_endpoint: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    langsmith_project: Optional[str] = None

    class Config:
        env_file = "../.env"
        extra = "allow"  # Allow extra fields from .env
        case_sensitive = False  # Make field matching case-insensitive


settings = Settings()