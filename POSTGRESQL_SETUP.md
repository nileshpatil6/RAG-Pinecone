# PostgreSQL Setup

The app defaults to SQLite for local development. For production (or to
avoid container filesystem permission issues on Render), switch to PostgreSQL.

## Local development with PostgreSQL

```bash
# Using Docker
docker run -d \
  --name rag-postgres \
  -e POSTGRES_DB=student_notes \
  -e POSTGRES_USER=rag_user \
  -e POSTGRES_PASSWORD=localpassword \
  -p 5432:5432 \
  postgres:15

# Then update .env
DATABASE_URL=postgresql+asyncpg://rag_user:localpassword@localhost:5432/student_notes
```

## Render PostgreSQL Setup

### The Problem
SQLite file permissions are causing issues in the containerized Render environment. The most reliable solution is to use PostgreSQL instead.

## Quick PostgreSQL Setup (Recommended)

### Step 1: Create PostgreSQL Database in Render

1. Go to your [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `student-notes-db`
   - **Database**: `student_notes`
   - **User**: `student_notes_user`
   - **Region**: Same as your web service
   - **PostgreSQL Version**: 15 (latest)
   - **Plan**: Free tier is fine for testing

4. Click **"Create Database"**

5. Once created, copy the **External Database URL** (it looks like):
   ```
   postgresql://user:password@host:port/database
   ```

### Step 2: Update Your Web Service Environment Variables

1. Go to your web service in Render Dashboard
2. Go to **Environment** tab
3. **Replace** the DATABASE_URL with your PostgreSQL URL:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
   ```

### Step 3: Redeploy

Your app will automatically redeploy and use PostgreSQL instead of SQLite.

## Benefits of PostgreSQL

✅ **No file permission issues**  
✅ **Data persists across deployments**  
✅ **Better performance for production**  
✅ **Concurrent access support**  
✅ **Full SQL feature support**  

## Alternative: SQLite Fixes

If you still want to use SQLite, the latest code includes:

1. **Absolute path**: `sqlite+aiosqlite:////tmp/app_student_notes.db`
2. **Fallback to in-memory**: If file creation fails
3. **Better error handling**: More detailed error messages
4. **Production detection**: Automatic path correction

But PostgreSQL is the recommended approach for production deployments.
