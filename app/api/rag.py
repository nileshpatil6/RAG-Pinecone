from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated, List
import json

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_rag_service
from app.models.database import User, Document as DocumentDB, UsageMetrics
from app.models.rag import (
    UploadResponse, QueryRequest, QueryResponse, 
    DocumentInfo, UsageStats, ChunkMetadata
)
from app.services.file_processor import FileProcessor
from app.core.rag import RAGService
import structlog
from datetime import datetime

router = APIRouter(prefix="/api", tags=["rag"])
logger = structlog.get_logger()


@router.post("/upload_notes", response_model=UploadResponse)
async def upload_notes(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    rag_service: Annotated[RAGService, Depends(get_rag_service)] = None
):
    """Upload and process student notes"""
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file
    processor = FileProcessor()
    is_valid, file_type_or_error = FileProcessor.validate_file(file.filename, file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=file_type_or_error
        )
    
    file_type = file_type_or_error
    
    try:
        # Process file into chunks
        chunks = await processor.process_file(content, file.filename, file_type)
        
        # Generate document ID
        document_id = FileProcessor.generate_document_id(
            current_user.id, file.filename, content
        )
        
        # Convert chunks to format for RAG service
        chunk_dicts = [
            {
                'text': chunk.text,
                'filename': file.filename,
                'page': chunk.metadata.get('page', 0)
            }
            for chunk in chunks
        ]
        
        # Upsert chunks to Pinecone
        chunk_count = await rag_service.upsert_chunks(
            current_user.id, document_id, chunk_dicts
        )
        
        # Save document record
        doc = DocumentDB(
            id=document_id,
            user_id=current_user.id,
            filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            chunk_count=chunk_count
        )
        db.add(doc)
        
        # Update usage metrics
        today = datetime.utcnow().date()
        
        # Query for existing metrics using a proper filter
        from sqlalchemy import select
        stmt = select(UsageMetrics).where(
            UsageMetrics.user_id == current_user.id,
            UsageMetrics.date == today
        )
        result = await db.execute(stmt)
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            metrics = UsageMetrics(
                user_id=current_user.id,
                date=today,
                tokens_used=0,
                embeddings_created=0,
                queries_made=0,
                read_units=0,
                write_units=0
            )
            db.add(metrics)
        
        # Ensure fields are not None before incrementing
        metrics.embeddings_created = (metrics.embeddings_created or 0) + chunk_count
        metrics.write_units = (metrics.write_units or 0) + chunk_count
        
        await db.commit()
        
        await logger.ainfo(
            "document_uploaded",
            user_id=current_user.id,
            document_id=document_id,
            filename=file.filename,
            chunks=chunk_count
        )
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            chunks_created=chunk_count,
            message=f"Successfully processed {chunk_count} chunks from {file.filename}"
        )
        
    except Exception as e:
        logger.error("upload_error", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )


@router.post("/ask")
async def ask_question(
    request: QueryRequest,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    rag_service: Annotated[RAGService, Depends(get_rag_service)] = None
):
    """Ask a question and get streaming answer"""
    try:
        # Retrieve relevant context
        context_results = await rag_service.retrieve_context(
            current_user.id,
            request.query,
            request.top_k
        )
        
        if not context_results:
            return QueryResponse(
                query=request.query,
                answer="No relevant information found in your notes.",
                sources=[],
                tokens_used=0
            )
        
        # Generate streaming response
        async def generate():
            # Send initial metadata
            metadata = {
                "query": request.query,
                "sources": [
                    {
                        "document_id": r.metadata.document_id,
                        "filename": r.metadata.filename,
                        "chunk_index": r.metadata.chunk_index,
                        "page": r.metadata.page
                    }
                    for r in context_results
                ]
            }
            yield f"data: {json.dumps({'type': 'metadata', 'data': metadata})}\n\n"
            
            # Stream answer
            token_count = 0
            async for chunk in rag_service.generate_answer(request.query, context_results):
                token_count += len(chunk.split())
                yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'tokens': token_count})}\n\n"
        
        # Update usage metrics
        today = datetime.utcnow().date()
        
        # Query for existing metrics using a proper filter
        stmt = select(UsageMetrics).where(
            UsageMetrics.user_id == current_user.id,
            UsageMetrics.date == today
        )
        result = await db.execute(stmt)
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            metrics = UsageMetrics(
                user_id=current_user.id,
                date=today,
                tokens_used=0,
                embeddings_created=0,
                queries_made=0,
                read_units=0,
                write_units=0
            )
            db.add(metrics)
        
        # Ensure fields are not None before incrementing
        metrics.queries_made = (metrics.queries_made or 0) + 1
        metrics.read_units = (metrics.read_units or 0) + len(context_results)
        
        await db.commit()
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error("query_error", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents(
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """List all documents for current user"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(DocumentDB).where(DocumentDB.user_id == current_user.id)
    )
    documents = result.scalars().all()
    
    return [DocumentInfo.from_orm(doc) for doc in documents]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    rag_service: Annotated[RAGService, Depends(get_rag_service)] = None
):
    """Delete a document and its chunks"""
    from sqlalchemy import select
    
    # Verify document ownership
    result = await db.execute(
        select(DocumentDB).where(
            DocumentDB.id == document_id,
            DocumentDB.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from Pinecone
    success = await rag_service.delete_document(current_user.id, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document from vector store"
        )
    
    # Delete from database
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}


@router.get("/dashboard", response_model=UsageStats)
async def get_dashboard(
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    rag_service: Annotated[RAGService, Depends(get_rag_service)] = None
):
    """Get usage statistics and remaining free tier"""
    from sqlalchemy import select, func
    
    # Get aggregated metrics
    result = await db.execute(
        select(
            func.sum(UsageMetrics.tokens_used).label('total_tokens'),
            func.sum(UsageMetrics.embeddings_created).label('total_embeddings'),
            func.sum(UsageMetrics.queries_made).label('total_queries'),
            func.sum(UsageMetrics.read_units).label('total_ru'),
            func.sum(UsageMetrics.write_units).label('total_wu')
        ).where(UsageMetrics.user_id == current_user.id)
    )
    
    stats = result.one()
    
    # Get namespace stats from Pinecone
    namespace_stats = await rag_service.get_namespace_stats(current_user.id)
    
    # Calculate storage (rough estimate: 768 dims * 4 bytes * vectors)
    storage_bytes = namespace_stats['vector_count'] * 768 * 4
    storage_mb = storage_bytes / (1024 * 1024)
    
    # Free tier limits
    free_tier = {
        'storage_gb': (2048 - storage_mb / 1024) / 2048 * 100,  # 2GB limit
        'write_units': (2_000_000 - (stats.total_wu or 0)) / 2_000_000 * 100,  # 2M WU
        'read_units': (1_000_000 - (stats.total_ru or 0)) / 1_000_000 * 100,  # 1M RU
    }
    
    return UsageStats(
        user_id=current_user.id,
        total_tokens=stats.total_tokens or 0,
        total_embeddings=stats.total_embeddings or 0,
        total_queries=stats.total_queries or 0,
        read_units=stats.total_ru or 0,
        write_units=stats.total_wu or 0,
        vector_count=namespace_stats['vector_count'],
        storage_used_mb=storage_mb,
        free_tier_remaining=free_tier
    )