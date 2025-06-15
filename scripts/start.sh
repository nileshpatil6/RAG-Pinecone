#!/bin/bash

# Startup script for Render deployment

echo "Starting application setup..."

# Set environment variables to indicate production deployment
export DEPLOYMENT_ENV=production
export APP_ENV=production

# Override database URL to ensure it's writable with absolute path
export DATABASE_URL="sqlite+aiosqlite:////tmp/app_student_notes.db"

echo "Environment variables:"
echo "DATABASE_URL: $DATABASE_URL"
echo "PORT: $PORT"
echo "DEPLOYMENT_ENV: $DEPLOYMENT_ENV"
echo "APP_ENV: $APP_ENV"

# Create the database file with proper permissions
echo "Setting up database file..."
DB_FILE="/tmp/app_student_notes.db"

# Remove any existing database file to start fresh
if [ -f "$DB_FILE" ]; then
    rm -f "$DB_FILE"
    echo "Removed existing database file"
fi

# Create the database file and set permissions
touch "$DB_FILE"
chmod 666 "$DB_FILE"
echo "Created database file: $DB_FILE"

# Also remove any SQLite auxiliary files that might cause issues
rm -f "${DB_FILE}-wal" "${DB_FILE}-shm" 2>/dev/null || true

# List files to confirm
echo "Files in /tmp:"
ls -la /tmp/app_* 2>/dev/null || echo "No app files found yet"

# Run diagnostic script to check everything
echo "Running diagnostics..."
python scripts/diagnose.py

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
