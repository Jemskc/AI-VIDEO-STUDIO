from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Movie Studio"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_movie_studio"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Settings
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    PASSWORD_SALT_ROUNDS: int = 12

    # Storage
    STORAGE_PATH: str = "./storage/uploads"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173"

    # Worker Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
