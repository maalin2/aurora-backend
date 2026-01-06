from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI, Query, Request, HTTPException
import httpx

@asynccontextmanager
# prevent leaks
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.client = httpx.AsyncClient(timeout=30)
    print('startup: http client created')

    # start running requests
    yield

    await app.state.client.aclose()
    print('shutdown: http client closed')


app = FastAPI(lifespan=lifespan)

SOURCE = 'https://november7-730026606190.europe-west1.run.app/messages/'

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "status": "FastAPI running on python 3.14.2"
    }

@app.get('/search')
async def search(
        request: Request,
        q: str | None = Query(None),
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100)
        ) -> dict:
    client: httpx.AsyncClient = request.app.state.client

    try:
        response = await client.get(SOURCE)
        response.raise_for_status()

        data = response.json()

        messages = data.get('items', [])

        if q:
            q_lower= q.lower()
            messages = [
                m for m in messages
                if q_lower in m.get('message', '').lower()
            ]


        total = len(messages)
        start = (page - 1) * size
        end = start + size
        results = messages[start:end]

        return {
            'total': total,
            'page': page,
            'size': size,
            'results': results
        }

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"api error: {str(e)}")

