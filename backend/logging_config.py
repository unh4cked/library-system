"""Logging configuration for the library system."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import settings


def setup_logging() -> logging.Logger:
    """
    Configure application-wide logging with console and file handlers.
    
    Returns:
        Configured logger instance for the application.
    """
    # Create logger
    logger = logging.getLogger("library_system")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    simple_formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s"
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter if settings.is_production else detailed_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if not settings.is_testing:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = RotatingFileHandler(
            filename=log_dir / settings.log_file,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Logging configured - Level: {settings.log_level}, Environment: {settings.environment}")
    
    return logger


# Create application logger
app_logger = setup_logging()


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name, typically __name__ from the calling module.
        
    Returns:
        Logger instance.
    """
    if name:
        return logging.getLogger(f"library_system.{name}")
    return app_logger
