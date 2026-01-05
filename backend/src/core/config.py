import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "TcyberChatbot"
    DATABASE_URL: str = "sqlite:///./data/chatbot.db"
    SECRET_KEY: str = "change-me-in-production-super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    REDIS_URL: str = "redis://redis:6379"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    
    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/auth/google/callback"  # Frontend proxies this to backend

    # Usage Quotas
    QUOTA_FREE_DAILY_REQUESTS: int = 50
    QUOTA_FREE_DAILY_TOKENS: int = 10000

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore" 

settings = Settings()
