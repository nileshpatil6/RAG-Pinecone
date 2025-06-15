#!/usr/bin/env python3
"""
Database diagnostic script for deployment troubleshooting
"""
import os
import sys
import asyncio

# Add the app directory to Python path
sys.path.append('/app')

async def diagnose_database():
    print("=== Database Diagnostic ===")
    
    # Check environment
    print(f"Current working directory: {os.getcwd()}")
    print(f"USER: {os.environ.get('USER', 'unknown')}")
    print(f"HOME: {os.environ.get('HOME', 'unknown')}")
    print(f"RENDER: {os.environ.get('RENDER', 'not set')}")
    print(f"DEPLOYMENT_ENV: {os.environ.get('DEPLOYMENT_ENV', 'not set')}")
    print()
    
    # Check file permissions
    print("=== File System Check ===")
    directories_to_check = ['/tmp', '/app', '/tmp/db']
    
    for directory in directories_to_check:
        if os.path.exists(directory):
            stat = os.stat(directory)
            print(f"{directory}: exists, permissions: {oct(stat.st_mode)[-3:]}")
        else:
            print(f"{directory}: does not exist")
    
    # Test creating a file in /tmp
    try:
        test_file = "/tmp/test_write.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("/tmp: writable ✓")
    except Exception as e:
        print(f"/tmp: not writable ✗ - {e}")
    
    print()
    
    # Check configuration
    print("=== Configuration Check ===")
    try:
        from app.core.config import settings
        print(f"Original database_url: {settings.database_url}")
        print(f"Safe database_url: {settings.safe_database_url}")
        print(f"App environment: {settings.app_env}")
        print(f"Debug mode: {settings.debug}")
    except Exception as e:
        print(f"Configuration error: {e}")
    
    print()
    
    # Test database connection
    print("=== Database Connection Test ===")
    try:
        from app.core.database import engine
        
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("Database connection: successful ✓")
            
        await engine.dispose()
    except Exception as e:
        print(f"Database connection failed ✗: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_database())
