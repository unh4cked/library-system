"""Configuration management for the library system."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables with LIBRARY_ prefix."""
    
    # Application
    app_name: str = "Library System"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "sqlite:///./library.db"
    database_echo: bool = False
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300
    
    # Authentication
    password: str = "library"
    
    # API
    api_prefix: str = ""
    cors_origins: list[str] = ["*"]
    
    # Server
    host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_port: int = 5500
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "library.log"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    model_config = SettingsConfigDict(
        env_prefix="LIBRARY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() in ("production", "prod")
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment.lower() in ("testing", "test")
    
    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return bool(self.redis_url)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
