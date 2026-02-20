from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth
from app.core.database import engine, Base

# Create database tables (in production, use Alembic migrations)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Qmate API",
    description="Hybrid AI-Human Student Support System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Qmate API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
