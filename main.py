from fastapi import FastAPI
#import httpx

app: FastAPI = FastAPI()

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "status": "FastAPI running on python 3.14.2"
    }
