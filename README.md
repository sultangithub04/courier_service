# Courier & Logistics Management Platform — FastAPI Backend

Production-oriented FastAPI backend for a courier/logistics platform.

## Stack
- Python 3.12+
- FastAPI + Uvicorn
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2 + pydantic-settings
- JWT access/refresh tokens
- bcrypt password hashing
- Swagger/OpenAPI
- pytest

## Roles
`ADMIN`, `USER`, `DELIVERY_AGENT`

## Run locally (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# edit DATABASE_URL and JWT_SECRET_KEY
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

Swagger: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc
Health: http://127.0.0.1:8000/health

## PostgreSQL
Create the database first:
```sql
CREATE DATABASE courier_db;
```

Example:
`postgresql+psycopg://postgres:password@localhost:5432/courier_db`

## Migrations
```bash
alembic revision --autogenerate -m "your change"
alembic upgrade head
alembic downgrade -1
```
Never use `Base.metadata.create_all()` in production.

## Development seed
`python -m app.seed` creates:
- admin@example.com / Admin@123456
- user1@example.com / User@123456
- delivery1@example.com / Delivery@123456

These are development-only credentials. Change/remove them before production.

## API
All business endpoints use `/api/v1`.

Auth:
- POST `/api/v1/auth/signup`
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/refresh`
- POST `/api/v1/auth/logout`
- POST `/api/v1/auth/forgot-password`
- POST `/api/v1/auth/reset-password`
- GET `/api/v1/auth/me`

Shipments:
- POST `/api/v1/shipments`
- GET `/api/v1/shipments`
- GET `/api/v1/shipments/{id}`
- PATCH `/api/v1/shipments/{id}`
- DELETE `/api/v1/shipments/{id}`
- GET `/api/v1/shipments/{id}/tracking`
- POST `/api/v1/shipments/{id}/tracking`

Admin:
- users, customers, delivery agents, payments, shipment assignment/status, dashboard

Delivery agent:
- assigned shipments and delivery status updates

## Security
- Passwords are never stored in plain text.
- JWT secrets are environment variables.
- Backend enforces ownership and role authorization.
- Sort fields are whitelisted.
- Authentication endpoints have a simple in-process rate limiter suitable for development; use Redis-backed rate limiting for multi-instance production.
- Reset tokens are stored hashed and expire.
