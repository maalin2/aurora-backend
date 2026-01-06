import pytest
from httpx import ASGITransport, AsyncClient, Response
from fastapi.testclient import TestClient
from main import app

# test root 
@pytest.mark.asyncio
async def test_root_endpoint() -> None:
    transport: ASGITransport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        response: Response = await ac.get('/')

    assert response.status_code == 200
    assert "FastAPI running" in response.json()['status']


# test closing resources. TestClient has its own loop
def test_lifespan() -> None:
    with TestClient(app):
        assert hasattr(app.state, 'client')
        assert app.state.client.is_closed is False

    assert app.state.client.is_closed is True

