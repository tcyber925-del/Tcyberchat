"""
Contract tests for GET /api/search endpoint
Tests full-text search across documents and conversations
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_search_success():
    """Test successful search query"""
    params = {"q": "artificial intelligence"}

    response = client.get("/api/search", params=params)

    # Should fail until endpoint is implemented
    assert response.status_code == 200
    response_data = response.json()

    # Validate response structure
    assert "query" in response_data
    assert "results" in response_data
    assert "total" in response_data
    assert response_data["query"] == "artificial intelligence"
    assert isinstance(response_data["results"], list)
    assert isinstance(response_data["total"], int)


def test_search_with_type_filter():
    """Test search with type filtering"""
    params = {"q": "machine learning", "type": "documents"}

    response = client.get("/api/search", params=params)

    assert response.status_code == 200
    response_data = response.json()

    # All results should be documents
    for result in response_data["results"]:
        assert result["type"] == "document"


def test_search_with_limit():
    """Test search with result limit"""
    params = {"q": "data", "limit": 5}

    response = client.get("/api/search", params=params)

    assert response.status_code == 200
    response_data = response.json()

    # Should not exceed the limit
    assert len(response_data["results"]) <= 5


def test_search_empty_query():
    """Test search with empty query string"""
    params = {"q": ""}

    response = client.get("/api/search", params=params)

    # Should return validation error
    assert response.status_code == 422


def test_search_no_matches():
    """Test search query with no expected matches"""
    params = {"q": "nonexistentterm12345"}

    response = client.get("/api/search", params=params)

    assert response.status_code == 200
    response_data = response.json()

    # Should return empty results
    assert len(response_data["results"]) == 0
    assert response_data["total"] == 0


def test_search_result_structure():
    """Test that search results have correct structure"""
    params = {"q": "test"}

    response = client.get("/api/search", params=params)

    assert response.status_code == 200
    response_data = response.json()

    # Validate result item structure
    for result in response_data["results"]:
        assert "type" in result
        assert "id" in result
        assert "title" in result
        assert "snippet" in result
        assert "score" in result
        assert result["type"] in ["document", "conversation"]
        assert isinstance(result["score"], (int, float))
