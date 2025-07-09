from fastapi import APIRouter, Depends
from app.schemas.invoices import InvoiceRequest
from app.services.invoice_service import generate_invoice_service
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/generate-invoice")
def generate_invoice(data: InvoiceRequest, current_user: str = Depends(get_current_user)):
    """Generate invoice endpoint"""
    # Pass the current user to the service for user-specific operations
    return generate_invoice_service(data, current_user)
