from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.config import settings
from app.models.database import User
from app.models.auth import TokenData

logger = structlog.get_logger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> tuple[str, datetime]:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
        to_encode = data.copy()
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt, expire
    
    @staticmethod
    async def decode_token(token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            if user_id is None:
                return None
            return TokenData(user_id=user_id, email=email)
        except JWTError:
            return None
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    async def create_user(db: AsyncSession, email: str, password: str, full_name: Optional[str] = None) -> User:
        hashed_password = AuthService.get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        await logger.ainfo("user_created", user_id=user.id, email=user.email)
        return user
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def save_refresh_token(db: AsyncSession, user_id: str, refresh_token: str, expires: datetime) -> None:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.refresh_token = refresh_token
            user.refresh_token_expires = expires
            await db.commit()
    
    @staticmethod
    async def validate_refresh_token(db: AsyncSession, refresh_token: str) -> Optional[User]:
        try:
            payload = jwt.decode(refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            if payload.get("type") != "refresh":
                return None
                
            user_id: str = payload.get("sub")
            if not user_id:
                return None
                
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or user.refresh_token != refresh_token:
                return None
                
            if user.refresh_token_expires < datetime.now(timezone.utc):
                return None
                
            return user
        except JWTError:
            return None