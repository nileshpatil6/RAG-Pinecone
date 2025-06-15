from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Token management
    refresh_token = Column(Text, nullable=True)
    refresh_token_expires = Column(DateTime(timezone=True), nullable=True)


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True, nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    document_metadata = Column(Text, nullable=True)  # JSON string


class UsageMetrics(Base):
    __tablename__ = "usage_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True, nullable=False)
    date = Column(DateTime(timezone=True), default=datetime.utcnow)
    tokens_used = Column(Integer, default=0)
    embeddings_created = Column(Integer, default=0)
    queries_made = Column(Integer, default=0)
    read_units = Column(Integer, default=0)
    write_units = Column(Integer, default=0)