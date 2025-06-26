from fastapi import APIRouter
from app.schemas.invoices import InvoiceRequest
from app.services.invoice_service import generate_invoice_service

router = APIRouter()

@router.post("/generate-invoice")
def generate_invoice(data: InvoiceRequest):
    """Generate invoice endpoint"""
    return generate_invoice_service(data)
