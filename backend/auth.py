"""Simple authentication module for the library system."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from .config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBasic()

# Load password from settings (consistent with config management)
LIBRARY_PASSWORD = settings.password


class LoginRequest(BaseModel):
    """Schema for login request."""

    password: str


class LoginResponse(BaseModel):
    """Schema for login response."""

    success: bool
    message: str


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    """
    Authenticate user with password.
    
    Note: This is a simple password-based authentication.
    For production, consider implementing JWT tokens or OAuth.
    """
    if payload.password == LIBRARY_PASSWORD:
        return LoginResponse(success=True, message="ورود موفقیت‌آمیز")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز عبور اشتباه است",
        )


@router.get("/check", response_model=dict[str, str])
def check_auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> dict[str, str]:
    """
    Check authentication with HTTP Basic Auth.
    
    This endpoint is for future use with proper authentication.
    """
    if credentials.password == LIBRARY_PASSWORD:
        return {"status": "authenticated"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect password",
        headers={"WWW-Authenticate": "Basic"},
    )
