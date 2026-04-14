#!/bin/bash

# Startup script for Render deployment

set -e

echo "[start] Configuring production environment..."

export DEPLOYMENT_ENV=production
export APP_ENV=production
export DATABASE_URL="sqlite+aiosqlite:////tmp/app_student_notes.db"

# Prepare writable SQLite file in /tmp (Render containers have read-only rootfs)
DB_FILE="/tmp/app_student_notes.db"
rm -f "${DB_FILE}-wal" "${DB_FILE}-shm" 2>/dev/null || true
touch "$DB_FILE" && chmod 666 "$DB_FILE"
echo "[start] Database file ready: $DB_FILE"

# Initialize database if it doesn't contain tables
echo "Checking database initialization..."
python -c "
import asyncio
import sys
import os
import sqlite3
sys.path.append('/app')

async def check_and_init_db():
    try:
        db_file = '/tmp/app_student_notes.db'
        
        # Check if the file can be opened with regular sqlite3 first
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
            tables = cursor.fetchall()
            conn.close()
            print(f'Direct SQLite check: found {len(tables)} tables')
        except Exception as e:
            print(f'Direct SQLite check failed: {e}')
            return
        
        # Now try with SQLAlchemy
        from app.core.database import engine
        from app.models.database import Base
        
        # Check if tables exist
        async with engine.begin() as conn:
            result = await conn.run_sync(lambda sync_conn: sync_conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())
            
        if not result:
            print('No tables found, initializing database...')
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print('Database initialized successfully')
        else:
            print(f'Database already contains {len(result)} tables')
            
        await engine.dispose()
    except Exception as e:
        print(f'Database setup error: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(check_and_init_db())
"

echo "Starting the application..."
# Start the application
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
