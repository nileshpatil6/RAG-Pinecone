# Deployment Guide for Render

## Prerequisites

1. **GitHub Repository**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **API Keys**: Have your Pinecone and Gemini API keys ready

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure these files are in your repository root:
- ✅ `Dockerfile` (updated with PORT variable support)
- ✅ `requirements.txt` (includes email-validator)
- ✅ `render.yaml` (optional, for easier setup)

### 2. Push Latest Changes

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 3. Create Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Choose **"Docker"** as the environment

### 4. Configure Service Settings

**Basic Settings:**
- **Name**: `student-notes-rag`
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Root Directory**: Leave blank (or specify if different)

**Build & Deploy:**
- **Runtime**: Docker
- **Build Command**: Auto-detected from Dockerfile
- **Start Command**: Auto-detected from Dockerfile

### 5. Set Environment Variables

In the Render dashboard, go to **Environment** tab and add these **secret** variables:

```env
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_PROJECT_ID=your_project_id_here
PINECONE_INDEX_NAME=student-notes
PINECONE_ENVIRONMENT=us-east-1
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET_KEY=your_super_secret_jwt_key_here
```

**IMPORTANT**: If you're having database permission issues, also add:
```env
DATABASE_URL=sqlite+aiosqlite:///tmp/student_notes.db
DEPLOYMENT_ENV=production
```

**Optional environment variables** (these have defaults):
```env
APP_ENV=production
DEBUG=false
MAX_UPLOAD_SIZE_MB=10
CHUNK_SIZE=400
TOP_K_RESULTS=8
```

### 6. Deploy

1. Click **"Create Web Service"**
2. Wait for the build to complete (5-10 minutes)
3. Your app will be available at: `https://your-service-name.onrender.com`

## Post-Deployment Checklist

### 1. Test Basic Functionality
- ✅ Visit your app URL
- ✅ Check `/health` endpoint
- ✅ Test `/docs` (API documentation)

### 2. Test Core Features
- ✅ User registration/login
- ✅ File upload
- ✅ Document querying
- ✅ Document management

### 3. Monitor Logs
- Check Render dashboard logs for any errors
- Monitor performance and response times

## Database Considerations

**Current Setup**: SQLite (file-based)
- ✅ **Pros**: Simple, no additional setup
- ⚠️ **Cons**: Data may be lost on redeploys, not suitable for high traffic, permission issues in containers

**For Production (Recommended)**: PostgreSQL
1. In Render Dashboard, create a new PostgreSQL database
2. Copy the database URL from Render
3. Update `DATABASE_URL` environment variable to the PostgreSQL URL
4. Install PostgreSQL driver: Add `asyncpg==0.29.0` to requirements.txt
5. Run migrations if needed

**Quick PostgreSQL Setup:**
```env
DATABASE_URL=postgresql+asyncpg://username:password@hostname:port/database_name
```

**SQLite Fix for Development:**
If sticking with SQLite, ensure it uses a writable directory:
```env
DATABASE_URL=sqlite+aiosqlite:///tmp/student_notes.db
```

## Troubleshooting Common Issues

### Build Failures
- Check if all dependencies are in `requirements.txt`
- Verify Dockerfile syntax
- Check build logs in Render dashboard

### Runtime Errors
- Ensure all required environment variables are set
- Check application logs for specific errors
- Verify API keys are valid and have required permissions

### Performance Issues
- Consider upgrading to a higher plan
- Monitor resource usage in dashboard
- Optimize database queries if needed

## Cost Optimization

1. **Free Tier**: Limited resources, good for testing
2. **Starter Plan**: $7/month, suitable for small applications
3. **Standard Plan**: $25/month, better performance

## Security Best Practices

1. ✅ Use environment variables for secrets
2. ✅ Enable HTTPS (automatic on Render)
3. ✅ Regularly rotate API keys
4. ✅ Monitor access logs

## Support Resources

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [GitHub Issues](https://github.com/your-repo/issues) for app-specific issues

---

## Quick Commands Reference

```bash
# Check deployment status
curl https://your-app.onrender.com/health

# View real-time logs (requires Render CLI)
render logs -s your-service-name

# Redeploy manually
# Go to Render dashboard → Manual Deploy
```

Your StudentNotesRAG application should now be successfully deployed on Render! 🚀
