# API Documentation

## Base URL

```
https://rag-pinecone.onrender.com
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"  // optional
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "student@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z",
  "is_active": true
}
```

### POST /auth/login

Login and receive JWT tokens.

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /auth/refresh

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

## Document Management

### POST /api/upload_notes

Upload and process a document.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: File upload (PDF, DOCX, or TXT)

**Response:**
```json
{
  "document_id": "doc_123",
  "filename": "lecture_notes.pdf",
  "chunks_created": 42,
  "message": "Successfully processed 42 chunks from lecture_notes.pdf"
}
```

### GET /api/documents

List all documents for the authenticated user.

**Response:**
```json
[
  {
    "id": "doc_123",
    "filename": "lecture_notes.pdf",
    "file_type": "pdf",
    "file_size": 1048576,
    "chunk_count": 42,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### DELETE /api/documents/{document_id}

Delete a document and all its chunks.

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

## Q&A

### POST /api/ask

Ask a question and receive streaming answer.

**Request Body:**
```json
{
  "query": "What are the main topics covered in Chapter 3?",
  "top_k": 8  // optional, default: 8, max: 20
}
```

**Response:** Server-Sent Events (SSE) stream
```
data: {"type": "metadata", "data": {"query": "...", "sources": [...]}}

data: {"type": "content", "data": "Based on your notes, Chapter 3 covers..."}

data: {"type": "content", "data": " the following main topics:\n\n1. ..."}

data: {"type": "done", "tokens": 150}
```

## Dashboard

### GET /api/dashboard

Get usage statistics and free tier remaining.

**Response:**
```json
{
  "user_id": "user_123",
  "total_tokens": 15000,
  "total_embeddings": 500,
  "total_queries": 50,
  "read_units": 50000,
  "write_units": 5000,
  "vector_count": 500,
  "storage_used_mb": 1.5,
  "free_tier_remaining": {
    "storage_gb": 99.9,      // percentage remaining
    "write_units": 99.75,    // percentage remaining
    "read_units": 95.0       // percentage remaining
  }
}
```

## Health Check

### GET /health

Check application health status.

**Response:**
```json
{
  "status": "healthy",
  "app": "StudentNotesRAG",
  "version": "1.0.0"
}
```

## Error Responses

All endpoints follow consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (inactive user)
- `404` - Not Found
- `422` - Unprocessable Entity (invalid request body)
- `500` - Internal Server Error