# Aurora Search API

A high-performance message search engine that queries an external data source and returns paginated results in under 100ms.

## What It Does

This API fetches message data from an external source on startup, caches it in-memory, and provides fast substring search with pagination. The prefetching approach eliminates external API latency from request handling, delivering results in under 100ms.

## Live Demo

API is deployed and publicly accessible:

```
http://ec2-18-188-23-166.us-east-2.compute.amazonaws.com:8000
```

- **Swagger docs**: `/docs`
- **Health check**: `/`
- **Search endpoint**: `/search?q=QUERY&page=1&size=10`

Example:
```
http://ec2-18-188-23-166.us-east-2.compute.amazonaws.com:8000/search?q=Paris
```

## Getting Started

### Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Server

```bash
uvicorn main:app --reload
```

Server runs on **http://localhost:8000**

## Endpoints

### GET `/`
Health check endpoint.

**Response:**
```json
{
  "status": "FastAPI running on python 3.14.2"
}
```

### GET `/search`
Search for messages by substring. Case-insensitive, supports pagination.

**Query Parameters:**
- `q` (optional, string): Search term. Searches within message content.
- `page` (optional, int, default=1): Page number (must be ≥1)
- `size` (optional, int, default=10): Results per page (1-100)

**Example:**
```
GET /search?q=Paris&page=1&size=20
```

**Response:**
```json
{
  "total": 4,
  "page": 1,
  "size": 20,
  "results": [
    {"message": "Hello from Paris"},
    {"message": "Paris is beautiful"},
    {"message": "Paris again"},
    {"message": "Back to Paris"}
  ]
}
```

## Testing

**Unit Tests** (fast, with mocks):
```bash
pytest test_main.py -v
```

**Integration Tests** (real API):
```bash
pytest test_integration.py -v
```

All tests run without mocking the lifespan, ensuring prefetch logic is tested end-to-end.

---

## Bonus 1: Design Notes

We considered several architectural approaches:

### Alternative 1: Django REST Framework
- **Pros**: Full-featured ORM, admin panel, batteries-included
- **Cons**: Heavyweight, overkill for simple search, slower startup
- **When to use**: Complex schemas, user management, long-term maintenance

### Alternative 2: Flask + Gunicorn
- **Pros**: Lightweight, familiar, easy to understand
- **Cons**: Synchronous by default, requires threading for async, more boilerplate
- **When to use**: Simple CRUD apps, team prefers minimal framework

### Alternative 3: Quart (Async Flask)
- **Pros**: Flask-like API but with async/await support
- **Cons**: Smaller ecosystem, less mature than FastAPI
- **When to use**: Teams wanting Flask simplicity with async

### Alternative 4: Raw ASGI (aiohttp)
- **Pros**: Lower-level control, minimal overhead, pure async
- **Cons**: Manual request/response handling, no validation helpers
- **When to use**: Performance-critical systems where framework overhead matters

### Alternative 5: Bottle
- **Pros**: Minimal single-file framework, quick prototypes
- **Cons**: No async support, limited built-in features
- **When to use**: Tiny microservices, educational projects

**Why FastAPI?**
- Modern Python async/await with Starlette
- Automatic API documentation (Swagger)
- Built-in validation and serialization
- Perfect balance of simplicity and features
- Fast development and easy testing

---

## Bonus 2: Reducing Latency to 30ms

Current performance: **<10ms per request** (already well below 100ms requirement)

To reach 30ms as a hard target (useful if requirements change), consider:

### Short Term (Quick Wins)
1. **Add response compression**: Gzip responses for faster transmission (~1-2ms saved)
   ```python
   from fastapi.middleware.gzip import GZipMiddleware
   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

2. **Implement client-side caching**: Cache results in browser for repeated queries
   ```python
   response.headers["Cache-Control"] = "max-age=300"
   ```

3. **Pre-sort/index data**: Sort messages by frequency, keep hot data in CPU cache

### Medium Term (Architecture Changes)
4. **Redis caching**: Cache frequent searches with TTL
   - Store top 100 search queries in Redis
   - Prefetch popular searches on startup
   - Adds ~2-3ms overhead but saves repeated filters

5. **Elasticsearch or similar**: Full-text search engine
   - Inverted indexes for instant substring matching
   - Distributed across multiple nodes
   - 30ms+ for complex queries, <5ms for simple ones

6. **Database with indexing**: Move to SQLite/PostgreSQL with LIKE indexes
   - Better than in-memory for very large datasets
   - EXPLAIN ANALYZE to optimize queries

### Advanced
7. **Request batching**: Allow clients to submit multiple queries in one request
8. **Precomputed results**: Generate common search results on data refresh
9. **Bloom filters**: Quick negative checks before expensive operations
10. **Edge deployment**: Run on CDN edge locations near users (latency from geography, not code)
