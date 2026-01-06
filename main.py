from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI, Query
import httpx

@asynccontextmanager
# prevent leaks
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.client = httpx.AsyncClient(timeout=10)
    print('startup: http client created')

    # start running requests
    yield

    await app.state.client.aclose()
    print('shutdown: http client closed')


app: FastAPI = FastAPI(lifespan=lifespan)

SOURCE = 'https://november7-730026606190.europe-west1.run.app/messages'

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "status": "FastAPI running on python 3.14.2"
    }
