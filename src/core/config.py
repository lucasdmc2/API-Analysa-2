"""
Application configuration using Pydantic Settings
Follows 12-Factor App principles with environment variables
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "API de Extração e Normalização de Exames Clínicos"
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_ECHO: bool = Field(default=False, env="DB_ECHO")
    
    # Redis Cache
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # AWS Configuration
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    S3_BUCKET_NAME: str = Field(..., env="S3_BUCKET_NAME")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    
    # OCR Configuration
    OCR_SERVICE: str = Field(default="textract", env="OCR_SERVICE")  # textract, tesseract
    OCR_CONFIDENCE_THRESHOLD: float = Field(default=0.8, env="OCR_CONFIDENCE_THRESHOLD")
    
    # Processing Configuration
    MAX_FILE_SIZE_MB: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    PIPELINE_VERSION: str = Field(default="1.0.0", env="PIPELINE_VERSION")
    PROCESSING_TIMEOUT_SECONDS: int = Field(default=300, env="PROCESSING_TIMEOUT_SECONDS")
    
    # Rate Limiting
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    STRUCTURED_LOGGING: bool = Field(default=True, env="STRUCTURED_LOGGING")
    
    # OAuth2/OIDC
    OAUTH2_TOKEN_URL: str = Field(..., env="OAUTH2_TOKEN_URL")
    OAUTH2_AUDIENCE: str = Field(..., env="OAUTH2_AUDIENCE")
    OAUTH2_ISSUER: str = Field(..., env="OAUTH2_ISSUER")
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()