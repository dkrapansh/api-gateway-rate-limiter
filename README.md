# API Gateway with Rate Limiting

A deployed production-style API gateway that authenticates clients via API keys, enforces fixed-window rate limiting, and routes requests to downstream services — with full quota visibility through standard rate limit headers.

## Live System

Backend: https://api-gateway-rate-limiter.onrender.com  
API Docs: https://api-gateway-rate-limiter.onrender.com/docs

## Overview

This project implements the gateway layer pattern used in real microservices architectures. Every request passes through a single entry point that handles authentication, rate limiting, and request logging before reaching any downstream service.

- Clients register to receive a cryptographically secure API key
- The key is hashed with SHA-256 before storage, raw credentials are never persisted
- Every request is authenticated and checked against a per-key rate limit (5 requests/min)
- Rate limit headers are returned on every response so clients can self-throttle
- Compromised keys can be revoked instantly via a dedicated endpoint
- Every request is logged with its target endpoint for per-key observability

## Features

- API key generation using Python's `secrets` module (cryptographically secure)
- SHA-256 hashing before storage:  raw key shown exactly once at creation
- Key revocation via `is_active` flag: disables access without losing request history
- Fixed-window rate limiting enforced via timestamp-based PostgreSQL queries
- Standard rate limit headers on every response: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- `Retry-After` header on 429 responses
- Per-request endpoint logging for downstream observability
- 409 Conflict on duplicate registration instead of 500 crash
- 401 vs 403 distinction: unknown key vs revoked key
- Mock downstream services (users, orders, products) simulating a microservices backend
- Auto-documented endpoints via Swagger UI

## Tech Stack

**Backend**
- FastAPI
- PostgreSQL
- SQLAlchemy

**Security**
- API key authentication
- SHA-256 one-way hashing (`hashlib`)
- Cryptographic key generation (`secrets`)

**Deployment**
- Render (Backend + PostgreSQL)

## Design Highlights

### API Key Security
Keys are generated using `secrets.token_hex(32)`: 256 bits of entropy from the OS-level cryptographically secure random source. Only the SHA-256 hash is stored. The raw key is returned to the client once and never saved anywhere. If lost, the user must generate a new key. This mirrors how Stripe and GitHub handle API credentials.

### Rate Limiting
Fixed-window rate limiting enforced by counting `RequestLog` entries for the current key within the last 60 seconds. If the count reaches the limit, the request is rejected with a 429. The window slides from the current timestamp, not from clock-aligned minutes.

### Rate Limit Headers
Every response, whether successful or not, includes:
- `X-RateLimit-Limit`: maximum requests allowed per window
- `X-RateLimit-Remaining`: requests left in the current window
- `X-RateLimit-Reset`: Unix timestamp when the window resets
- `Retry-After`: seconds to wait (on 429 responses only)

This gives clients full visibility into their quota so they can self-throttle before hitting a wall.

### Key Revocation
Revoking a key sets `is_active = False` on the `rl_api_keys` table. The key is rejected at the auth layer immediately with a 403 Forbidden. All historical request logs for that key are preserved — soft delete maintains the audit trail.

### Endpoint Logging
Each `RequestLog` row stores the target endpoint path alongside the key ID and timestamp. This supports per-key per-service observability — you can see not just how many requests a key made, but which downstream services it was hitting.

### Shared Database Design
This project shares a PostgreSQL instance with another deployed project. All tables are prefixed with `rl_` (rate-limiter) to prevent naming conflicts. Both projects coexist safely in one database.

## Project Structure

```
api-gateway-rate-limiter/
│
├── app/
│   ├── __init__.py
│   ├── main.py        # routes, rate limiting logic, gateway enforcer
│   ├── models.py      # SQLAlchemy models (User, APIKey, RequestLog)
│   ├── database.py    # engine, session, base
│   └── utils.py       # key generation and hashing
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

## API Endpoints

### Registration
- `POST /register` — Register with email, receive a one-time API key

### Key Management
- `POST /keys/revoke` — Revoke your API key (pass key in `X-API-Key` header)

### Protected Gateway Routes
All routes below require a valid `X-API-Key` header.

- `GET /protected`  Base protected route
- `GET /gateway/users`   Mock user service
- `GET /gateway/orders`   Mock order service
- `GET /gateway/products`   Mock product service

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/dkrapansh/api-gateway-rate-limiter
cd api-gateway-rate-limiter
```

### 2. Create and activate virtual environment

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add environment variables

Create a `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost:5432/your_db
```

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

API will run at: http://127.0.0.1:8000  
Swagger docs: http://127.0.0.1:8000/docs

## Workflow

### Register and get a key
1. `POST /register` with your email
2. Copy the returned `api_key`, it will not be shown again

### Make authenticated requests
Pass your key in the `X-API-Key` header on every request to `/gateway/*` routes.

### Monitor your quota
Check `X-RateLimit-Remaining` in the response headers after each request.

### Revoke a compromised key
`POST /keys/revoke` with the key in the `X-API-Key` header. The key is invalidated immediately.

## Known Trade-offs

**Fixed-window vs sliding-window rate limiting**  
Fixed-window is simpler and cheaper, one COUNT query per request. A client can theoretically send 5 requests at the end of one window and 5 at the start of the next, pushing 10 through in a short burst. Sliding-window or token bucket algorithms solve this but require Redis for atomic operations. PostgreSQL is sufficient at this scale; Redis would be the right call at high traffic.

**Race condition in check-then-log**  
The rate limit check and the log insert are separate operations. Two simultaneous requests can both pass the count check before either writes a log entry. The fix is a database-level lock or Redis INCR for atomic check-and-increment. The consequence at this scale is minor — one extra request gets through. This is a conscious, documented trade-off.

## Future Improvements

- Redis-backed rate limiting for atomic operations and sliding-window accuracy
- Alembic migrations instead of `create_all()`
- Multiple keys per user
- Per-route rate limit configuration
- Admin dashboard for key management and request analytics
- Dockerized deployment

## Why I Built This

I built this to understand how production API gateways work at the implementation level and not just the concept. Auth, rate limiting, observability, and key lifecycle management are cross-cutting concerns that every backend system needs. Building them from scratch in a gateway pattern made every design decision explicit: why hash and not encrypt, why soft delete and not hard delete, why return headers on success and not just on 429. The goal was to build something that caters a real backend use case.

## Author

Krapansh Dubey  
github.com/dkrapansh
