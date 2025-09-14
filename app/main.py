import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, orders, invoices, plan_status, profile, reports
from app.core.config import settings

# Configure logging from env
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Voice Backend", version="1.0.0")

# Add CORS middleware from env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOWED_METHODS,
    allow_headers=settings.CORS_ALLOWED_HEADERS,
)

# Include routers
# app.include_router(transcription.router, tags=["transcription"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
app.include_router(profile.router)
app.include_router(plan_status.router)
app.include_router(reports.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Order Voice Backend API", "version": "1.0.0"}