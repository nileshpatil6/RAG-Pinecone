import pytest
from app.services.file_processor import FileProcessor
from app.models.rag import DocumentChunk


class TestFileProcessor:
    @pytest.fixture
    def processor(self):
        return FileProcessor()
    
    def test_token_length(self, processor):
        """Test token counting functionality"""
        text = "This is a simple test text."
        token_count = processor._token_length(text)
        assert token_count > 0
        assert isinstance(token_count, int)
    
    def test_clean_text(self, processor):
        """Test text cleaning functionality"""
        dirty_text = "This   has\n\nextra    spaces… and "special" quotes."
        clean_text = processor._clean_text(dirty_text)
        
        assert "..." in clean_text
        assert '"' in clean_text
        assert "  " not in clean_text
    
    @pytest.mark.asyncio
    async def test_process_txt_file(self, processor):
        """Test processing of TXT files"""
        content = b"This is a test document. It contains multiple sentences. " * 50
        chunks = await processor.process_file(content, "test.txt", "txt")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(chunk.metadata['filename'] == "test.txt" for chunk in chunks)
    
    def test_validate_file_valid(self):
        """Test file validation with valid file"""
        is_valid, result = FileProcessor.validate_file("document.pdf", 1024 * 1024)  # 1MB
        assert is_valid
        assert result == "pdf"
    
    def test_validate_file_invalid_type(self):
        """Test file validation with invalid file type"""
        is_valid, error = FileProcessor.validate_file("document.exe", 1024)
        assert not is_valid
        assert "not allowed" in error
    
    def test_validate_file_too_large(self):
        """Test file validation with oversized file"""
        is_valid, error = FileProcessor.validate_file("document.pdf", 100 * 1024 * 1024)  # 100MB
        assert not is_valid
        assert "exceeds" in error
    
    def test_generate_document_id(self):
        """Test document ID generation"""
        doc_id = FileProcessor.generate_document_id("user123", "test.pdf", b"content")
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0
        
        # Should be deterministic
        doc_id2 = FileProcessor.generate_document_id("user123", "test.pdf", b"content")
        assert doc_id == doc_id2