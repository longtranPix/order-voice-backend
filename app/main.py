from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.routes import (
    auth_router,
    transcription_router,
    orders_router,
    invoices_router
)

# Setup logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(auth_router)
app.include_router(transcription_router)
app.include_router(orders_router)
app.include_router(invoices_router)

# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Order Voice Backend API",
        "version": settings.APP_VERSION,
        "status": "healthy"
    }