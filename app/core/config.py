from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="StudentNotesRAG")
    app_version: str = Field(default="1.0.0")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Pinecone
    pinecone_api_key: str
    pinecone_project_id: str
    pinecone_index_name: str = Field(default="student-notes")
    pinecone_environment: str = Field(default="us-east-1")
    
    # Google Gemini
    gemini_api_key: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)
    
    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///tmp/student_notes.db")
    
    @property
    def safe_database_url(self) -> str:
        """Ensure database URL points to a writable location"""
        db_url = self.database_url
        
        # If it's SQLite and pointing to current directory, redirect to /tmp
        if "sqlite" in db_url.lower():
            # For production/container environments, always use /tmp with full path
            if (os.environ.get("RENDER") or 
                os.environ.get("DEPLOYMENT_ENV") == "production" or
                self.app_env == "production"):
                
                # First try /tmp with absolute path
                try_url = "sqlite+aiosqlite:////tmp/app_student_notes.db"
                
                # Test if we can create a file in /tmp
                try:
                    import sqlite3
                    test_conn = sqlite3.connect("/tmp/test_db_access.db")
                    test_conn.close()
                    os.remove("/tmp/test_db_access.db")
                    return try_url
                except:
                    # If /tmp doesn't work, fall back to in-memory database
                    # This will lose data on restart but at least the app will run
                    return "sqlite+aiosqlite:///:memory:"
            elif not db_url.startswith("sqlite+aiosqlite:////tmp/"):
                # Ensure it uses absolute path in /tmp
                return "sqlite+aiosqlite:////tmp/app_student_notes.db"
        
        return db_url
    
    # File Upload
    max_upload_size_mb: int = Field(default=10)
    allowed_file_types_str: str = Field(default="pdf,docx,txt", alias="allowed_file_types")
    
    @property
    def allowed_file_types(self) -> list[str]:
        return [item.strip() for item in self.allowed_file_types_str.split(',')]
    
    # RAG Configuration
    chunk_size: int = Field(default=400)
    chunk_overlap: int = Field(default=50)
    embedding_dimension: int = Field(default=768)
    top_k_results: int = Field(default=8)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    # OpenTelemetry
    otel_exporter_otlp_endpoint: Optional[str] = Field(default=None)
    otel_service_name: str = Field(default="student-notes-rag")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()