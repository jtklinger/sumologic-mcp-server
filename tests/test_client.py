"""Tests for Sumo Logic client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sumologic_mcp_server.client import SumoLogicClient, SearchJob, SearchResult


@pytest.fixture
def client():
    """Create a test client."""
    return SumoLogicClient("test_id", "test_key", "https://test.sumologic.com/api")


@pytest.mark.asyncio
async def test_create_search_job(client):
    """Test creating a search job."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "test-job-123",
        "state": "GATHERING RESULTS"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        job = await client.create_search_job("test query", "-1h", "now")
        
        assert job.id == "test-job-123"
        assert job.state == "GATHERING RESULTS"
        assert job.query == "test query"


@pytest.mark.asyncio
async def test_get_search_job_status(client):
    """Test getting search job status."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "test-job-123",
        "state": "DONE GATHERING RESULTS",
        "messageCount": 100,
        "recordCount": 50
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        job = await client.get_search_job_status("test-job-123")
        
        assert job.id == "test-job-123"
        assert job.state == "DONE GATHERING RESULTS"
        assert job.message_count == 100
        assert job.record_count == 50


@pytest.mark.asyncio
async def test_get_search_job_records(client):
    """Test getting search job records."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "records": [
            {"field1": "value1", "field2": "value2"},
            {"field1": "value3", "field2": "value4"}
        ],
        "fields": [
            {"name": "field1", "fieldType": "string"},
            {"name": "field2", "fieldType": "string"}
        ],
        "totalCount": 2
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await client.get_search_job_records("test-job-123")
        
        assert len(result.records) == 2
        assert len(result.fields) == 2
        assert result.total_count == 2
        assert result.job_id == "test-job-123"