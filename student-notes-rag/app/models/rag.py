from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChunkMetadata(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    page: Optional[int] = 0
    
    
class QueryResult(BaseModel):
    chunk_id: str
    score: float
    text: str
    metadata: ChunkMetadata


class DocumentChunk(BaseModel):
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    message: str


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = Field(None, ge=1, le=20)


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[ChunkMetadata]
    tokens_used: Optional[int] = None


class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UsageStats(BaseModel):
    user_id: str
    total_tokens: int
    total_embeddings: int
    total_queries: int
    read_units: int
    write_units: int
    vector_count: int
    storage_used_mb: float
    free_tier_remaining: Dict[str, float]