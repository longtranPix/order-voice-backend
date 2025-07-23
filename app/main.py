import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import transcription, auth, orders, invoices, import_slips, customers, products, unit_conversions, suppliers, plan_status, user_profile

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
app.include_router(transcription.router, tags=["transcription"])
app.include_router(auth.router, tags=["authentication"])
app.include_router(orders.router, tags=["orders"])
app.include_router(invoices.router, tags=["invoices"])
app.include_router(import_slips.router, tags=["import_slips"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(unit_conversions.router, prefix="/unit-conversions", tags=["unit_conversions"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
app.include_router(plan_status.router)
app.include_router(user_profile.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Order Voice Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks"""
    return {
        "status": "healthy",
        "service": "Order Voice Backend",
        "version": "1.0.0"
    }