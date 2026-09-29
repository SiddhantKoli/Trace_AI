import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "TRACE AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./trace_ai.db"
    
    # Jev AI API Settings
    JEV_API_KEY: str = os.getenv("JEV_API_KEY", "")
    JEV_API_URL: str = "https://api.typesafe.ai/v1/systemone"
    DEMO_MODE: bool = True  # Default to deterministic demo mode if no key provided
    
    # ML & Anomaly Detection Defaults
    DEFAULT_CONTAMINATION: float = 0.08
    DEFAULT_CORRELATION_WINDOW_SECONDS: int = 120
    
    # Ingestion Limits
    MAX_FILE_SIZE_MB: int = 25
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()

# Check if a live API key was explicitly set
if settings.JEV_API_KEY and settings.JEV_API_KEY.strip() != "":
    settings.DEMO_MODE = False
