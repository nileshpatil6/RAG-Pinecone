from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.core.database import get_db
from app.models.auth import UserRegister, UserLogin, Token, RefreshTokenRequest, UserResponse
from app.services.auth import AuthService
import structlog

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = structlog.get_logger()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Register a new user"""
    # Check if user already exists
    existing_user = await AuthService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = await AuthService.create_user(
        db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    return UserResponse.from_orm(user)


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Login and receive access/refresh tokens"""
    user = await AuthService.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = AuthService.create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    
    refresh_token, expires = AuthService.create_refresh_token(
        data={"sub": user.id, "email": user.email}
    )
    
    # Save refresh token
    await AuthService.save_refresh_token(db, user.id, refresh_token, expires)
    
    await logger.ainfo("user_login", user_id=user.id, email=user.email)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Refresh access token using refresh token"""
    user = await AuthService.validate_refresh_token(db, request.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens
    access_token = AuthService.create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    
    refresh_token, expires = AuthService.create_refresh_token(
        data={"sub": user.id, "email": user.email}
    )
    
    # Update refresh token
    await AuthService.save_refresh_token(db, user.id, refresh_token, expires)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )