from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI, Query, Request, HTTPException
import httpx

SOURCE = 'https://november7-730026606190.europe-west1.run.app/messages/'

@asynccontextmanager
# prevent leaks
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.client = httpx.AsyncClient(timeout=30)
    print('startup: http client created')

    # prefetch data from external API on startup
    try:
        response = await app.state.client.get(SOURCE)
        response.raise_for_status()
        data = response.json()
        app.state.messages = data.get('items', [])
        print(f'startup: prefetched {len(app.state.messages)} messages')
    except Exception as e:
        print(f'startup: error prefetching data: {e}')
        raise

    # start running requests
    yield

    await app.state.client.aclose()
    print('shutdown: http client closed')


app = FastAPI(lifespan=lifespan)

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
    messages = request.app.state.messages

    if q:
        q_lower = q.lower()
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

