#!/bin/bash

# Startup script for Render deployment

echo "Starting application setup..."

# Set environment variable to indicate production deployment
export DEPLOYMENT_ENV=production

# Override database URL to ensure it's writable
export DATABASE_URL="sqlite+aiosqlite:///tmp/student_notes.db"

echo "Environment variables:"
echo "DATABASE_URL: $DATABASE_URL"
echo "PORT: $PORT"
echo "DEPLOYMENT_ENV: $DEPLOYMENT_ENV"

# Create necessary directories with proper permissions
echo "Creating writable directories..."
mkdir -p /tmp/db
chmod 755 /tmp/db

# Ensure /tmp directory is writable
chmod 755 /tmp

# Create database file with proper permissions if it doesn't exist
if [ ! -f "/tmp/student_notes.db" ]; then
    echo "Creating new database file..."
    touch /tmp/student_notes.db
    chmod 664 /tmp/student_notes.db
fi

# Run diagnostic script to check everything
echo "Running diagnostics..."
python scripts/diagnose.py

# Initialize database if it doesn't contain tables
echo "Checking database initialization..."
python -c "
import asyncio
import sys
import os
sys.path.append('/app')

async def check_and_init_db():
    try:
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
        # Continue anyway, let the app handle it

asyncio.run(check_and_init_db())
"

echo "Starting the application..."
# Start the application
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
