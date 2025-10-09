"""Entry point for the FastAPI application of the library system backend."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from . import auth
from .config import settings
from .database import Base, SessionLocal, engine
from .models import DEFAULT_CATEGORIES
from .exceptions import (
    LibraryException,
    database_exception_handler,
    general_exception_handler,
    integrity_exception_handler,
    library_exception_handler,
    validation_exception_handler,
)
from .logging_config import get_logger
from .models import Category
from .routers import books, loans, students

logger = get_logger(__name__)


def initialize_default_categories() -> None:
    """Create default categories if they don't exist."""
    db = SessionLocal()
    try:
        for cat_data in DEFAULT_CATEGORIES:
            # Check if category already exists
            statement = select(Category).where(Category.name == cat_data["name"])
            existing = db.execute(statement).scalar_one_or_none()
            if existing is None:
                category = Category(**cat_data)
                db.add(category)
                logger.info(f"Created default category: {cat_data['name']}")
        db.commit()
    except Exception as e:
        logger.error(f"Failed to initialize categories: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan events.
    
    Startup:
        - Create database tables
        - Initialize default categories
        - Log application info
        
    Shutdown:
        - Log shutdown message
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info("Creating database tables if they do not exist")
    Base.metadata.create_all(bind=engine)
    logger.info("Initializing default categories")
    initialize_default_categories()
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    
    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title=settings.app_name,
        description="Backend API for managing library books, students, and loans",
        version=settings.app_version,
        lifespan=lifespan,
        debug=settings.debug,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Exception handlers
    app.add_exception_handler(LibraryException, library_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Include routers
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(books.router, prefix=settings.api_prefix)
    app.include_router(students.router, prefix=settings.api_prefix)
    app.include_router(loans.router, prefix=settings.api_prefix)

    @app.get("/", tags=["health"], summary="Health check")
    async def health_check() -> dict[str, str]:
        """
        Basic health check endpoint.
        
        Returns:
            Status message.
        """
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }

    @app.get("/health", tags=["health"], summary="Detailed health check")
    async def detailed_health_check() -> dict[str, Any]:
        """
        Detailed health check with service statuses.
        
        Returns:
            Detailed health information.
        """
        from datetime import datetime
        from .cache import get_redis_client
        
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "operational",
            }
        }
        
        # Check database
        try:
            db = SessionLocal()
            db.execute(select(1))
            db.close()
            health["services"]["database"] = "operational"
        except Exception as e:
            health["services"]["database"] = f"error: {str(e)}"
            health["status"] = "degraded"
        
        # Check Redis
        try:
            redis = get_redis_client()
            if redis:
                redis.ping()
                health["services"]["redis"] = "operational"
            else:
                health["services"]["redis"] = "disabled"
        except Exception as e:
            health["services"]["redis"] = f"error: {str(e)}"
        
        return health

    logger.info("FastAPI application created and configured")
    return app


app = create_app()
