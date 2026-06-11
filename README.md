![CI](https://github.com/dkrapansh/api-gateway-rate-limiter/actions/workflows/ci.yml/badge.svg)

# API Gateway with Rate Limiting

A production-structured API gateway built with FastAPI and PostgreSQL. Clients authenticate via API keys, requests are rate limited per key using a sliding window algorithm, and every request is logged for observability. The project is layered into separate routes, schemas, services, and dependencies following real backend architecture patterns.

## Live System

Backend: https://api-gateway-rate-limiter.onrender.com  
API Docs: https://api-gateway-rate-limiter.onrender.com/docs

## What This Does

Every request to this gateway goes through a single entry point that handles authentication, rate limiting, request logging, and routing before reaching any downstream service.

- Clients register with an email and receive a cryptographically secure API key
- The key is hashed with SHA-256 before storage, raw credentials are never persisted
- Every request is authenticated and rate limited (5 requests per 60 second sliding window per key)
- Rate limit headers are returned on every response so clients can self-throttle
- Compromised keys can be revoked instantly, audit history is preserved
- Every request is logged with its target endpoint for per-key observability
- Usage analytics available per key showing request counts broken down by endpoint

## Tech Stack

- FastAPI, SQLAlchemy, PostgreSQL
- Alembic for schema migrations
- pytest + TestClient for integration tests
- Docker and Docker Compose for local setup
- GitHub Actions CI running tests on every push
- Render for hosting

## Project Structure

```
api-gateway-rate-limiter/
├── app/
│   ├── main.py           # app setup and router registration
│   ├── config.py         # typed settings via Pydantic BaseSettings
│   ├── database.py       # engine, session, base
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic request and response schemas
│   ├── dependencies.py   # auth dependency and rate limiting logic
│   ├── middleware.py      # correlation ID middleware
│   ├── utils.py          # key generation and hashing
│   └── routes/
│       ├── auth.py       # register and revoke endpoints
│       ├── gateway.py    # protected downstream routes
│       ├── health.py     # health check endpoint
│       └── analytics.py  # usage analytics endpoint
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_gateway.py
│   ├── test_rate_limiting.py
│   ├── test_revocation.py
│   ├── test_middleware.py
│   ├── test_health.py
│   └── test_analytics.py
├── alembic/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## API Endpoints

### Auth
- `POST /register` — register with email, receive a one-time API key
- `POST /keys/revoke` — revoke your key (pass key in `X-API-Key` header)

### Gateway Routes (require `X-API-Key` header)
- `GET /protected` — base protected route
- `GET /gateway/users` — mock user service
- `GET /gateway/orders` — mock order service
- `GET /gateway/products` — mock product service

### Observability
- `GET /health` — health check with real DB connectivity verification
- `GET /analytics/usage` — per-key request stats broken down by endpoint

## Local Setup

### Option 1: Docker (recommended)

```bash
git clone https://github.com/dkrapansh/api-gateway-rate-limiter
cd api-gateway-rate-limiter
docker-compose up
```

App runs at http://localhost:8000 and Swagger docs at http://localhost:8000/docs.

### Option 2: Manual

```bash
git clone https://github.com/dkrapansh/api-gateway-rate-limiter
cd api-gateway-rate-limiter
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost:5432/your_db
```

Run migrations and start:
```bash
alembic upgrade head
uvicorn app.main:app --reload
```

## Running Tests

```bash
pytest tests/ -v
```

Tests run against an in-memory SQLite database via dependency override. No real database needed.

## Design Decisions

### API Key Security
Keys are generated with `secrets.token_hex(32)`, giving 256 bits of entropy from the OS-level cryptographically secure random source. Only the SHA-256 hash is stored. The raw key is shown once at creation and never saved anywhere. If lost, the user generates a new key. This is the same pattern Stripe and GitHub use for API credentials.

SHA-256 is used instead of bcrypt because API keys are already high-entropy random strings. bcrypt is for low-entropy human passwords. Hashing a high-entropy secret with SHA-256 is standard practice and significantly faster.

### Sliding Window Rate Limiting
Rate limiting counts `RequestLog` entries for the current key where the timestamp falls within the last 60 seconds from the current request. This is a true sliding window, not a clock-aligned fixed window. Fixed-window has a known burst edge case where a client can send 2x the limit across a window boundary. The sliding window eliminates this.

### Race Condition Fix
The rate limit check and the log insert are two separate operations. Two concurrent requests can both read the same count before either writes. This is fixed with `SELECT FOR UPDATE` which acquires a row-level lock before reading, serialising concurrent access. A unique constraint at the database level acts as a second failsafe.

### Rate Limit Headers
Every response includes `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`. The 429 response additionally includes `Retry-After`. Returning headers on successful responses (not just 429s) lets clients self-throttle before hitting the limit. This is how Stripe, GitHub, and Twitter handle it.

### Key Revocation
Revoking a key sets `is_active = False`. The key fails at the auth layer immediately with a 403 Forbidden. All historical request logs are preserved. Hard deleting a key would cascade and destroy the audit trail, which is the wrong trade-off.

### Correlation IDs
Every request gets a UUID correlation ID, either from an incoming `X-Correlation-ID` header or freshly generated. It is attached to request state, included in all log lines, and returned in the response header. In production this lets you grep logs by a single ID and see the complete request trace.

## Known Limitations

**PostgreSQL rate limiting at scale:** The current rate limit check involves a DB query on every request. At high traffic this becomes a bottleneck. The fix is Redis with atomic `INCR` and `EXPIRE` operations, which handles this at O(1) in-memory speed. PostgreSQL is correct and sufficient at this project's scale.

**Mock downstream services:** The gateway routes return stub data. In a real system these would proxy to internal services using an async HTTP client like httpx, with credential stripping and service-to-service token injection.

## Author

Krapansh Dubey  
github.com/dkrapansh