# RAG-Pinecone

[![CI](https://github.com/nileshpatil6/RAG-Pinecone/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nileshpatil6/RAG-Pinecone/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Production-ready Retrieval-Augmented Generation (RAG) system for student notes with Q&A capabilities.

## Features

- 🔐 **JWT Authentication** with refresh tokens
- 📄 **Multi-format Support**: PDF, DOCX, TXT file processing
- 🧠 **AI-Powered Q&A**: Using Google Gemini for embeddings and answers
- 📊 **Usage Dashboard**: Track tokens, storage, and free-tier limits
- 🔍 **Namespace Isolation**: Each student sees only their own data
- 📈 **Production Ready**: Structured logging, OpenTelemetry, Docker support

## Tech Stack

- **Backend**: Python 3.11, FastAPI, async/await
- **Vector DB**: Pinecone (serverless, us-east-1)
- **AI Models**: Google Gemini (embeddings & chat)
- **Auth**: JWT with PyJWT
- **Database**: SQLite/PostgreSQL (user management)
- **Logging**: structlog + OpenTelemetry

## Quick Start

### Prerequisites

1. Python 3.11+
2. Pinecone account (free tier)
3. Google Cloud account with Gemini API access

### Installation

1. Clone the repository:
```bash
git clone https://github.com/nileshpatil6/RAG-Pinecone.git
cd RAG-Pinecone
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
make install
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Required environment variables:
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_PROJECT_ID`: Pinecone project ID
- `GEMINI_API_KEY`: Google Gemini API key
- `JWT_SECRET_KEY`: Secret key for JWT tokens (generate a strong random string)

### Running Locally

Development mode:
```bash
make dev
```

Production mode:
```bash
make run
```

Docker:
```bash
make docker-build
make docker-run
```

## API Endpoints

### Authentication

**Register**
```bash
curl -X POST https://rag-pinecone.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "student@example.com", "password": "securepass123"}'
```

**Login**
```bash
curl -X POST https://rag-pinecone.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student@example.com", "password": "securepass123"}'
```

### Document Management

**Upload Notes**
```bash
curl -X POST https://rag-pinecone.onrender.com/api/upload_notes \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@notes.pdf"
```

**List Documents**
```bash
curl https://rag-pinecone.onrender.com/api/documents \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Q&A

**Ask Question** (Streaming Response)
```bash
curl -X POST https://rag-pinecone.onrender.com/api/ask \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key concepts in Chapter 3?"}'
```

### Dashboard

**Get Usage Stats**
```bash
curl https://rag-pinecone.onrender.com/api/dashboard \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Architecture

```
student-notes-rag/
├── app/
│   ├── api/          # FastAPI routes
│   ├── core/         # Core functionality (config, RAG, logging)
│   ├── models/       # Pydantic models & database schemas
│   ├── services/     # Business logic (auth, file processing)
│   └── main.py       # Application entry point
├── tests/            # Unit and integration tests
├── scripts/          # Utility scripts
├── docs/             # Additional documentation
└── notebooks/        # Jupyter notebooks (capacity calculator)
```

## Deployment

### Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/student-notes-rag

# Deploy
gcloud run deploy student-notes-rag \
  --image gcr.io/PROJECT-ID/student-notes-rag \
  --platform managed \
  --allow-unauthenticated
```

## Testing

Run tests:
```bash
make test
```

Linting:
```bash
make lint
```

Format code:
```bash
make format
```

## Monitoring

The application includes:
- Structured JSON logging with request IDs
- OpenTelemetry instrumentation (optional)
- Health check endpoint at `/health`
- Metrics tracking for usage and costs

## Security Considerations

- JWT tokens expire after 30 minutes (configurable)
- Refresh tokens expire after 7 days
- Each user has isolated namespace in Pinecone
- File size limits enforced (10MB default)
- Input validation on all endpoints
- Rate limiting recommended for production

## Capacity Planning

Free tier limits:
- **Pinecone**: 2GB storage, 2M write units, 1M read units/month
- **Gemini**: Check current Google Cloud quotas

Rough estimates per student:
- 100 pages ≈ 300-500 chunks
- Each chunk ≈ 3KB in Pinecone (768 dims × 4 bytes)
- 1000 students × 500 chunks = 1.5GB storage

## License

MIT License - see LICENSE file for details

## Support

For issues and feature requests, please use the GitHub issue tracker.