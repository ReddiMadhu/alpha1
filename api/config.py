"""API Configuration settings"""
from pydantic_settings import BaseSettings
from typing import List
import os


class APIConfig(BaseSettings):
    """Configuration for FastAPI application"""

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "Excel Relationship Discovery API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Discover relationships between Excel files using AI-powered analysis"

    # File Upload Settings
    MAX_FILE_SIZE_MB: int = 100
    MAX_FILES_PER_JOB: int = 5
    ALLOWED_EXTENSIONS: List[str] = [".xlsx", ".xls", ".xlsm", ".csv"]
    UPLOAD_DIR: str = "data/uploads"
    RESULT_DIR: str = "data/results"

    # Database Settings
    DATABASE_PATH: str = "data/jobs.db"

    # Job Execution Settings
    JOB_TIMEOUT_SECONDS: int = 600  # 10 minutes
    MAX_CONCURRENT_JOBS: int = 3

    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_PING_TIMEOUT: int = 60

    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]  # Configure for production
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Cleanup Settings
    DELETE_FILES_ON_JOB_DELETE: bool = True
    AUTO_CLEANUP_OLD_JOBS_DAYS: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def ensure_directories(self):
        """Ensure all required directories exist"""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.RESULT_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.DATABASE_PATH), exist_ok=True)


# Global config instance
config = APIConfig()
