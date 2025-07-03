# backend/app/core/config.py (create this file)
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI API Key for GPT-4
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Other settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "allow"  # This allows all your existing .env variables

# Create settings instance
settings = Settings()
