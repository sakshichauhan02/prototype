from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aetheria Companion Core Engine"
    API_V1_STR: str = "/api/v1"
    
    # Security config keys
    SECRET_KEY: str = "aetheria-super-secret-crypto-elliptic-quantum-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Async database URL configuration (defaults to a local sqlite or postgresql pool)
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./aetheria.db",
        validation_alias="DATABASE_URL"
    )
    GEMINI_API_KEY: str = Field(
        default="",
        validation_alias="GEMINI_API_KEY"
    )
    QDRANT_PATH: str = "./qdrant_data"
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""
    NEWS_API_KEY: str = ""
    N8N_WEBHOOK_URL: str = ""
    MAKE_WEBHOOK_URL: str = ""

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
