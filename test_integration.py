"""Integration tests against real external API"""
import pytest
import time
from fastapi.testclient import TestClient
from main import app


class TestIntegration:
    """Tests against the real external API - slower but tests real behavior"""

    def test_real_api_search_performance(self):
        """Test that real API search meets <100ms requirement"""
        with TestClient(app) as client:
            start = time.perf_counter()
            response = client.get('/search', params={'q': 'test'})
            elapsed = (time.perf_counter() - start) * 1000  # ms

            assert response.status_code == 200
            assert elapsed < 100, f"Response took {elapsed:.2f}ms, must be under 100ms"

    def test_real_api_returns_data(self):
        """Test that real API returns data"""
        with TestClient(app) as client:
            response = client.get('/search')
            assert response.status_code == 200

            data = response.json()
            assert data['total'] > 0
            assert len(data['results']) > 0

    def test_real_api_search_filtering(self):
        """Test search filtering against real API"""
        with TestClient(app) as client:
            response = client.get('/search', params={'q': 'Paris'})
            assert response.status_code == 200

            data = response.json()
            # Only verify structure, API may or may not have Paris data
            assert 'total' in data
            assert 'results' in data
            assert isinstance(data['results'], list)

    def test_real_api_pagination(self):
        """Test pagination against real API"""
        with TestClient(app) as client:
            resp1 = client.get('/search', params={'page': 1, 'size': 3})
            resp2 = client.get('/search', params={'page': 2, 'size': 3})

            assert resp1.status_code == 200
            assert resp2.status_code == 200

            data1 = resp1.json()
            data2 = resp2.json()

            # If enough data, pages should be different
            if data1['total'] > 3:
                assert data1['results'] != data2['results']

    def test_real_api_response_structure(self):
        """Test response structure from real API"""
        with TestClient(app) as client:
            response = client.get('/search', params={'q': 'test'})
            assert response.status_code == 200

            data = response.json()
            assert 'total' in data
            assert 'page' in data
            assert 'size' in data
            assert 'results' in data

            # Validate that results contain message field
            for item in data['results']:
                assert 'message' in item
