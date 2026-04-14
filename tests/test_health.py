"""
Tests for health check and root endpoints — no API keys required.
These run in CI without any external service credentials.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock


@pytest.fixture
def mock_settings(monkeypatch):
    """Patch settings so the app loads without real API keys."""
    monkeypatch.setenv("PINECONE_API_KEY", "test-key")
    monkeypatch.setenv("PINECONE_PROJECT_ID", "test-project")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-for-testing-only")


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(mock_settings):
    """GET /health must return 200 with status:healthy."""
    with (
        patch("app.core.database.init_db", new_callable=AsyncMock),
        patch("app.core.database.close_db", new_callable=AsyncMock),
        patch("app.core.rag.RAGService.__init__", return_value=None),
    ):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert "version" in body


@pytest.mark.asyncio
async def test_root_returns_app_info(mock_settings):
    """GET / must return app info when no static/index.html is present."""
    with (
        patch("app.core.database.init_db", new_callable=AsyncMock),
        patch("app.core.database.close_db", new_callable=AsyncMock),
        patch("app.core.rag.RAGService.__init__", return_value=None),
        patch("pathlib.Path.exists", return_value=False),
    ):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/")

        assert response.status_code == 200
        body = response.json()
        assert "app" in body
        assert body["docs"] == "/docs"
