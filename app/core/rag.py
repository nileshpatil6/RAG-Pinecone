import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import structlog
from tenacity import retry, wait_exponential, stop_after_attempt
import hashlib
import json

from app.core.config import settings
from app.models.rag import DocumentChunk, QueryResult, ChunkMetadata

logger = structlog.get_logger()


class RAGService:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.chat_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self._ensure_index()
        self.index = self.pc.Index(settings.pinecone_index_name)
    
    def _ensure_index(self):
        """Ensure Pinecone index exists with correct configuration"""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if settings.pinecone_index_name not in existing_indexes:
            self.pc.create_index(
                name=settings.pinecone_index_name,
                dimension=settings.embedding_dimension,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region=settings.pinecone_environment
                )
            )
            logger.info("created_pinecone_index", index=settings.pinecone_index_name)
    
    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text using Gemini"""
        try:
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error("embedding_error", error=str(e), text_preview=text[:100])
            raise
    
    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    async def embed_query(self, query: str) -> List[float]:
        """Generate embeddings for query using Gemini"""
        try:
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error("query_embedding_error", error=str(e), query=query)
            raise
    
    def _generate_chunk_id(self, user_id: str, doc_id: str, chunk_index: int) -> str:
        """Generate deterministic chunk ID"""
        content = f"{user_id}:{doc_id}:{chunk_index}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def upsert_chunks(
        self, 
        user_id: str, 
        document_id: str,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """Upsert document chunks to Pinecone"""
        vectors = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = self._generate_chunk_id(user_id, document_id, i)
            embedding = await self.embed_text(chunk['text'])
            
            metadata = {
                'user_id': user_id,
                'document_id': document_id,
                'chunk_index': i,
                'text': chunk['text'],
                'filename': chunk.get('filename', ''),
                'page': chunk.get('page', 0),
                'total_chunks': len(chunks)
            }
            
            vectors.append({
                'id': chunk_id,
                'values': embedding,
                'metadata': metadata
            })
        
        # Batch upsert to Pinecone
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            await asyncio.to_thread(
                self.index.upsert,
                vectors=batch,
                namespace=user_id
            )
        
        await logger.ainfo(
            "chunks_upserted",
            user_id=user_id,
            document_id=document_id,
            chunk_count=len(chunks)
        )
        
        return len(chunks)
    
    async def retrieve_context(
        self,
        user_id: str,
        query: str,
        top_k: int = None
    ) -> List[QueryResult]:
        """Retrieve relevant chunks for a query"""
        if top_k is None:
            top_k = settings.top_k_results
            
        query_embedding = await self.embed_query(query)
        
        results = await asyncio.to_thread(
            self.index.query,
            namespace=user_id,
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        query_results = []
        for match in results['matches']:
            result = QueryResult(
                chunk_id=match['id'],
                score=match['score'],
                text=match['metadata']['text'],
                metadata=ChunkMetadata(
                    document_id=match['metadata']['document_id'],
                    filename=match['metadata']['filename'],
                    chunk_index=match['metadata']['chunk_index'],
                    page=match['metadata'].get('page', 0)
                )
            )
            query_results.append(result)
        
        await logger.ainfo(
            "context_retrieved",
            user_id=user_id,
            query=query[:100],
            results_count=len(query_results)
        )
        
        return query_results
    
    async def generate_answer(
        self,
        query: str,
        context: List[QueryResult]
    ) -> AsyncIterator[str]:
        """Generate streaming answer using retrieved context"""
        
        # Build context string with citations
        context_parts = []
        for i, result in enumerate(context):
            citation = f"[{i+1}]"
            context_parts.append(
                f"{citation} From {result.metadata.filename} (page {result.metadata.page}):\n"
                f"{result.text}\n"
            )
        
        full_context = "\n---\n".join(context_parts)
        
        prompt = f"""You are a helpful AI assistant answering questions based on the provided student notes.

Context from the student's notes:
{full_context}

Student's Question: {query}

Instructions:
1. Answer based ONLY on the provided context
2. Include citation numbers [1], [2], etc. when referencing specific information
3. If the context doesn't contain enough information, say so clearly
4. Be concise but thorough
5. Use markdown formatting for better readability

Answer:"""

        try:
            response = await asyncio.to_thread(
                self.chat_model.generate_content,
                prompt,
                stream=True,
                generation_config={
                    'temperature': 0.7,
                    'max_output_tokens': 2048,
                }
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error("generation_error", error=str(e))
            yield f"Error generating response: {str(e)}"
    
    async def delete_document(self, user_id: str, document_id: str) -> bool:
        """Delete all chunks for a document"""
        try:
            # First, query to get all vector IDs for this document
            query_response = await asyncio.to_thread(
                self.index.query,
                namespace=user_id,
                vector=[0.0] * settings.embedding_dimension,  # Dummy vector
                top_k=10000,  # Get all vectors
                include_metadata=True,
                filter={"document_id": {"$eq": document_id}}
            )
            
            # Extract vector IDs to delete
            vector_ids = [match['id'] for match in query_response.get('matches', [])]
            
            if vector_ids:
                # Delete vectors by ID
                await asyncio.to_thread(
                    self.index.delete,
                    ids=vector_ids,
                    namespace=user_id
                )
                
                await logger.ainfo(
                    "document_deleted",
                    user_id=user_id,
                    document_id=document_id,
                    deleted_chunks=len(vector_ids)
                )
            else:
                await logger.ainfo(
                    "no_chunks_found_for_deletion",
                    user_id=user_id,
                    document_id=document_id
                )
            
            return True
        except Exception as e:
            logger.error("delete_document_error", error=str(e))
            return False
    
    async def get_namespace_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user's namespace"""
        try:
            stats = await asyncio.to_thread(
                self.index.describe_index_stats,
                namespace=user_id
            )
            
            namespace_stats = stats.get('namespaces', {}).get(user_id, {})
            return {
                'vector_count': namespace_stats.get('vector_count', 0),
                'total_index_vectors': stats.get('total_vector_count', 0),
                'dimension': stats.get('dimension', settings.embedding_dimension)
            }
        except Exception as e:
            logger.error("get_stats_error", error=str(e))
            return {
                'vector_count': 0,
                'total_index_vectors': 0,
                'dimension': settings.embedding_dimension
            }