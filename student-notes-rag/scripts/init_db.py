#!/usr/bin/env python3
"""Initialize the database with tables"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init_db, engine
from app.models.database import Base
import structlog

logger = structlog.get_logger()


async def main():
    """Initialize database tables"""
    try:
        await init_db()
        logger.info("Database initialized successfully")
        
        # List all tables
        async with engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: Base.metadata.tables.keys()
            )
            logger.info("Created tables", tables=list(tables))
            
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())