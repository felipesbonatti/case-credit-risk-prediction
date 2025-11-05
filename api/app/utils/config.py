"""
Configuration settings with dynamic path resolution
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List

# Determine base directory dynamically
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Set PROJECT_ROOT for environment variable expansion
PROJECT_ROOT = str(BASE_DIR)
DATA_PATH = os.getenv("DATA_PATH", str(BASE_DIR / "data" / "processed"))

# Expand ${PROJECT_ROOT} in DATA_PATH if present
if "${PROJECT_ROOT}" in DATA_PATH:
    DATA_PATH = DATA_PATH.replace("${PROJECT_ROOT}", PROJECT_ROOT)


class Settings(BaseSettings):
    """
    Application settings with universal path support
    """

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ENV: str = "local"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = True

    # Security (valor padrão para desenvolvimento)
    SECRET_KEY: str = "santander-credit-risk-secret-key-dev-2025-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "postgresql://santander:santander123@postgres:5432/credit_risk"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://:redis123@redis:6379/0"
    CACHE_TTL: int = 3600
    CACHE_MAX_SIZE: int = 1000

    # ML Model (dynamic paths)
    MODEL_PATH: str = str(BASE_DIR / "api" / "modelo_lgbm.pkl")
    MODEL_VERSION: str = "1.0.0"
    THRESHOLD_DEFAULT: float = 0.50
    N_FEATURES: int = 15

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 100

    # Monitoring
    METRICS_ENABLED: bool = True

    # Feature Flags
    FEATURE_EXPLAINABILITY: bool = True
    FEATURE_MONITORING: bool = True

    # Data Path (from environment or default)
    DATA_PATH_OVERRIDE: str = DATA_PATH

    model_config = ConfigDict(env_file=str(BASE_DIR / ".env"), case_sensitive=True, extra="ignore")


# Create settings instance
settings = Settings()

# Export useful paths
PROJECT_ROOT_PATH = BASE_DIR
DATA_PATH_RESOLVED = Path(DATA_PATH)
