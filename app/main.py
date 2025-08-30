import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import transcription, auth, orders, invoices

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Voice Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# app.include_router(transcription.router, tags=["transcription"])
app.include_router(auth.router, tags=["authentication"])
app.include_router(orders.router, tags=["orders"])
app.include_router(invoices.router, tags=["invoices"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Order Voice Backend API", "version": "1.0.0"}