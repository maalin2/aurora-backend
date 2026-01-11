"""Unit tests with mocked external API"""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from main import app

# Mock data for external API
MOCK_MESSAGES = {
    'items': [
        {'message': 'Hello from Paris'},
        {'message': 'Testing in London'},
        {'message': 'Paris is beautiful'},
        {'message': 'Another test message'},
        {'message': 'Paris again'},
        {'message': 'Something else'},
        {'message': 'Final test'},
        {'message': 'Back to Paris'},
        {'message': 'More data'},
        {'message': 'Last item'},
    ]
}


@pytest.fixture
def mock_external_api(monkeypatch):
    """Mock the external API call"""
    async def mock_get(*args, **kwargs):
        mock_resp = AsyncMock()
        mock_resp.json = lambda: MOCK_MESSAGES  # json() is sync
        mock_resp.raise_for_status = lambda: None  # sync method
        return mock_resp

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    return mock_get


# ===== Core functionality tests =====

def test_pagination(mock_external_api) -> None:
    """Test pagination with different page numbers"""
    with TestClient(app) as client:
        response = client.get('/search', params={'page': 2, 'size': 2})
        assert response.status_code == 200

        data = response.json()
        assert data['page'] == 2
        assert len(data['results']) <= 2


def test_filtering(mock_external_api) -> None:
    """Test search filtering returns only matching results"""
    with TestClient(app) as client:
        response = client.get('/search', params={'q': 'Paris'})
        assert response.status_code == 200
        data = response.json()

        assert data['total'] > 0
        for item in data['results']:
            assert 'paris' in item['message'].lower()


def test_no_results(mock_external_api) -> None:
    """Test search with no matching results"""
    with TestClient(app) as client:
        response = client.get('/search', params={'q': 'aoisfhaoishfoiashfioashfoa'})
        assert response.status_code == 200
        data = response.json()

        assert data['total'] == 0
        assert data['results'] == []


def test_search_no_filter(mock_external_api) -> None:
    """Test search without filter returns all data"""
    with TestClient(app) as client:
        response = client.get('/search')
        assert response.status_code == 200

        data = response.json()
        assert data['total'] > 0
        assert len(data['results']) > 0


# ===== Response structure tests =====

def test_response_structure(mock_external_api) -> None:
    """Test response contains all required fields with correct types"""
    with TestClient(app) as client:
        response = client.get('/search', params={'q': 'test'})
        assert response.status_code == 200

        data = response.json()
        assert 'total' in data
        assert 'page' in data
        assert 'size' in data
        assert 'results' in data
        assert isinstance(data['total'], int)
        assert isinstance(data['page'], int)
        assert isinstance(data['size'], int)
        assert isinstance(data['results'], list)


# ===== Pagination tests =====

def test_pagination_consistency(mock_external_api) -> None:
    """Test that different pages return different results"""
    with TestClient(app) as client:
        resp1 = client.get('/search', params={'page': 1, 'size': 5})
        data1 = resp1.json()

        resp2 = client.get('/search', params={'page': 2, 'size': 5})
        data2 = resp2.json()

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        if data1['total'] > 5:
            assert data1['results'] != data2['results']


def test_size_parameter_limits(mock_external_api) -> None:
    """Test that size parameter correctly limits results"""
    with TestClient(app) as client:
        resp5 = client.get('/search', params={'size': 5})
        data5 = resp5.json()

        resp10 = client.get('/search', params={'size': 10})
        data10 = resp10.json()

        assert len(data5['results']) <= 5
        assert len(data10['results']) <= 10


def test_large_page_number(mock_external_api) -> None:
    """Test pagination with page number beyond available results"""
    with TestClient(app) as client:
        response = client.get('/search', params={'page': 999999})
        assert response.status_code == 200

        data = response.json()
        assert data['page'] == 999999
        assert data['results'] == []


# ===== Input validation tests =====

def test_invalid_page_zero(mock_external_api):
    """Test that page 0 is rejected"""
    with TestClient(app) as client:
        response = client.get('/search', params={'page': 0})
        assert response.status_code == 422


def test_invalid_size_zero(mock_external_api):
    """Test that size 0 is rejected"""
    with TestClient(app) as client:
        response = client.get('/search', params={'size': 0})
        assert response.status_code == 422


def test_invalid_size_too_large(mock_external_api):
    """Test that size > 100 is rejected"""
    with TestClient(app) as client:
        response = client.get('/search', params={'size': 101})
        assert response.status_code == 422


# ===== Edge cases =====

def test_whitespace_query(mock_external_api) -> None:
    """Test handling of whitespace-only query"""
    with TestClient(app) as client:
        response = client.get('/search', params={'q': '   '})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data['total'], int)


def test_case_insensitive_search(mock_external_api) -> None:
    """Test that search is case-insensitive"""
    with TestClient(app) as client:
        resp_lower = client.get('/search', params={'q': 'paris'})
        resp_upper = client.get('/search', params={'q': 'PARIS'})

        assert resp_lower.status_code == 200
        assert resp_upper.status_code == 200

        data_lower = resp_lower.json()
        data_upper = resp_upper.json()

        assert data_lower['total'] == data_upper['total']


def test_partial_match_search(mock_external_api) -> None:
    """Test that partial words match"""
    with TestClient(app) as client:
        response = client.get('/search', params={'q': 'Par'})
        assert response.status_code == 200
        data = response.json()
        assert data['total'] > 0
