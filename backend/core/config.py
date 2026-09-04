# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Groww App
    app_name: str = "Groww"
    platform: str = "Google Play"
    package_name: str = "com.nextbillion.groww"
    review_lookback_days: int = 7

    # Groq
    groq_api_key: str = ""
    groq_model_name: str = "qwen/qwen3.8-27b"
    groq_temperature: float = 0.1
    groq_max_tokens: int = 4096

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"
    google_doc_id: str = ""

    # Server
    backend_port: int = 8000
    frontend_port: int = 5173
    database_url: str = "sqlite:///./data/groww_intelligence.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
