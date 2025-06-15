# Deployment Guide

## Prerequisites

- Docker installed (for containerized deployment)
- Cloud provider account (Fly.io, Railway, or Google Cloud)
- Environment variables configured

## Local Deployment

### Using Docker

1. Build the image:
```bash
docker build -t student-notes-rag:latest .
```

2. Run with docker-compose:
```bash
docker-compose up -d
```

3. Check logs:
```bash
docker-compose logs -f app
```

### Without Docker

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```bash
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

3. Run the application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Cloud Deployment

### Fly.io (Recommended for Hackathons)

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Create `fly.toml`:
```toml
app = "student-notes-rag"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  APP_ENV = "production"
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[services]]
  protocol = "tcp"
  internal_port = 8000

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

3. Deploy:
```bash
fly launch
fly secrets set PINECONE_API_KEY=xxx GEMINI_API_KEY=xxx JWT_SECRET_KEY=xxx
fly deploy
```

### Railway

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

3. Deploy:
```bash
railway login
railway init
railway add
railway deploy
```

### Google Cloud Run

1. Enable required APIs:
```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com
```

2. Build and push image:
```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud builds submit --tag gcr.io/$PROJECT_ID/student-notes-rag
```

3. Deploy to Cloud Run:
```bash
gcloud run deploy student-notes-rag \
  --image gcr.io/$PROJECT_ID/student-notes-rag \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "APP_ENV=production" \
  --set-secrets "PINECONE_API_KEY=pinecone-key:latest,GEMINI_API_KEY=gemini-key:latest,JWT_SECRET_KEY=jwt-key:latest"
```

## Environment Variables

Create secrets for sensitive values:

### Fly.io
```bash
fly secrets set \
  PINECONE_API_KEY="your-key" \
  GEMINI_API_KEY="your-key" \
  JWT_SECRET_KEY="your-secret"
```

### Railway
Use the Railway dashboard to add environment variables.

### Google Cloud
```bash
# Create secrets
echo -n "your-pinecone-key" | gcloud secrets create pinecone-key --data-file=-
echo -n "your-gemini-key" | gcloud secrets create gemini-key --data-file=-
echo -n "your-jwt-secret" | gcloud secrets create jwt-key --data-file=-
```

## Post-Deployment

1. Test the health endpoint:
```bash
curl https://your-app.fly.dev/health
```

2. Initialize the database (if using PostgreSQL):
```bash
fly ssh console -C "python -m alembic upgrade head"
```

3. Monitor logs:
```bash
fly logs  # Fly.io
railway logs  # Railway
gcloud run logs read  # Cloud Run
```

## Production Considerations

### Database

For production, switch from SQLite to PostgreSQL:

1. Update `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

2. Install asyncpg:
```bash
pip install asyncpg
```

### Security

1. Use strong JWT secret:
```bash
openssl rand -hex 32
```

2. Enable CORS restrictions in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

3. Add rate limiting:
```bash
pip install slowapi
```

### Monitoring

1. Enable OpenTelemetry:
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-collector.com:4317
```

2. Set up alerts for:
- High error rates
- Slow response times
- Free tier usage approaching limits

### Scaling

1. Horizontal scaling:
- Fly.io: `fly scale count 2`
- Railway: Increase replicas in dashboard
- Cloud Run: Auto-scales by default

2. Database connection pooling:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)
```

### Backup

Regular backups for user data:
```bash
# SQLite
fly ssh console -C "sqlite3 student_notes.db .dump > backup.sql"

# PostgreSQL
pg_dump $DATABASE_URL > backup.sql
```