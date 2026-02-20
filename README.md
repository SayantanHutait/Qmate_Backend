# Qmate Backend

Hybrid AI-Human Student Support System Backend API.

## Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+ (via Docker)
- Redis (via Docker)

### Installation

1. **Clone and navigate to Backend directory:**
   ```bash
   cd Backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start PostgreSQL and Redis:**
   ```bash
   docker-compose up -d
   ```

6. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

7. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Project Structure

```
app/
├── api/              # API routes
├── core/             # Core utilities (security, database, config)
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
└── db/               # Database migrations
```

## Development

- Run tests: `pytest`
- Create migration: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`
