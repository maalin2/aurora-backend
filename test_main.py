import pytest
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient
from main import app

# test root 
def test_root_endpoint() -> None:
    with TestClient(app) as client:
        assert hasattr(app.state, 'client')
        assert app.state.client.is_closed is False

        response = client.get('/')

        assert response.status_code == 200
        assert "FastAPI running" in response.json()['status']

    assert app.state.client.is_closed is True

# test closing resources. TestClient has its own loop
def test_lifespan() -> None:
    with TestClient(app):
        assert hasattr(app.state, 'client')
        assert app.state.client.is_closed is False

    assert app.state.client.is_closed is True

# test pagination
def test_pagination() -> None:
    with TestClient(app) as client:
        assert hasattr(app.state, 'client')
        assert app.state.client.is_closed is False

        response = client.get('/search', params={'page': 2, 'size': 2})
        assert response.status_code == 200

        data = response.json()
        assert data['page'] == 2
        assert len(data['results']) <= 2

    assert app.state.client.is_closed is True

# test search for paris
def test_filtering() -> None:
    with TestClient(app) as client:
        assert hasattr(app.state, 'client')
        assert app.state.client.is_closed is False
        
        response = client.get('/search', params={'q': 'Paris'})
        assert response.status_code == 200
        data = response.json()

        assert data['total'] > 0
        for item in data['results']:
            assert 'paris' in item['message'].lower()

    assert app.state.client.is_closed is True

# test nonsense filter/search
def test_bad_filtering() -> None:
    with TestClient(app) as client:
        assert hasattr(app.state, 'client')
        assert app.state.client.is_closed is False
        
        response = client.get('/search', params={'q':
                                                 'aoisfhaoishfoiashfioashfoa'})
        assert response.status_code == 200
        data = response.json()

        assert data['total'] == 0
        assert data['results'] == []

    assert app.state.client.is_closed is True

# test validation
def test_invalid_bounds():
    with TestClient(app) as client:
        assert hasattr(app.state, 'client')
        assert app.state.client.is_closed is False

        resp_page = client.get('/search', params={'page': 0})
        assert resp_page.status_code == 422

        resp_size_small = client.get('/search', params={'size': 0})
        assert resp_size_small.status_code == 422

        resp_size_large = client.get('/search', params={'size': 101})
        assert resp_size_large.status_code == 422

    assert app.state.client.is_closed is True

