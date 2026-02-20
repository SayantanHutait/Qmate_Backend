# Phase 1 Setup Guide

## Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Git

## Step-by-Step Setup

### 1. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and update:
# - SECRET_KEY (generate a random 32+ character string)
# - DATABASE_URL (should match docker-compose.yml)
# - REDIS_URL (should match docker-compose.yml)
```

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 4. Start PostgreSQL and Redis
```bash
docker-compose up -d
```

Verify containers are running:
```bash
docker-compose ps
```

### 5. Run Database Migrations
```bash
# Create initial migration (already created, but you can create new ones with):
# alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### 6. Seed Initial Data (Optional)
```bash
python scripts/seed_data.py
```

This creates:
- Default departments (CS, Admin, Finance, Academic)
- Admin user: `admin@qmate.edu` / `admin123`

### 7. Start the Server
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Testing the API

### 1. Sign Up a New User
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123",
    "name": "Test Student",
    "role": "student"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123"
  }'
```

Response will include `access_token` and `refresh_token`.

### 3. Get Current User Info
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Refresh Token
```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check DATABASE_URL in `.env` matches docker-compose.yml
- Verify PostgreSQL is ready: `docker-compose logs postgres`

### Redis Connection Error
- Ensure Redis container is running: `docker-compose ps`
- Check REDIS_URL in `.env`

### Migration Errors
- Ensure PostgreSQL is running before migrations
- If tables already exist, you may need to drop them first (development only):
  ```bash
  # WARNING: This deletes all data!
  alembic downgrade base
  alembic upgrade head
  ```

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

## Next Steps

Phase 1 is complete! You can now:
- ✅ Sign up users
- ✅ Login and get JWT tokens
- ✅ Refresh tokens
- ✅ Get current user info

**Phase 2** will add:
- Conversations and Messages models
- REST API for conversations
- Message storage (no AI yet)
