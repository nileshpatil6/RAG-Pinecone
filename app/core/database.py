from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Log the database URL being used
logger.info("database_configuration", 
           original_url=settings.database_url,
           safe_url=settings.safe_database_url)

# Create async engine
engine = create_async_engine(
    settings.safe_database_url,
    echo=settings.debug,
    future=True
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("database_error", error=str(e))
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    try:
        from app.models.database import Base
        
        logger.info("initializing_database", url=settings.safe_database_url)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        # Re-raise the exception so the app startup fails if database can't be initialized
        raise


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("database_closed")