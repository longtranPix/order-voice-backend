import httpx
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import InvoiceRequest, InvoiceResponse
from app.services import TeableService, InvoiceService
from app.utils import get_http_client
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.post("/generate", response_model=InvoiceResponse)
async def generate_invoice(
    data: InvoiceRequest,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Generate invoice using Viettel API."""
    try:
        teable_service = TeableService()
        invoice_service = InvoiceService()
        
        # Step 1: Get invoice_token from Teable
        user_result = await teable_service.get_user_by_username(client, data.username)
        
        if not user_result["success"]:
            raise HTTPException(
                status_code=user_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=user_result.get("error", "Could not fetch user data")
            )
        
        records = user_result.get("data", {}).get("records", [])
        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in Teable"
            )
        
        invoice_token = records[0]["fields"].get("invoice_token")
        if not invoice_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No invoice_token found in user record"
            )
        
        # Step 2: Generate invoice
        invoice_result = await invoice_service.generate_invoice(
            client, data.username, invoice_token, data.invoice_payload
        )
        
        if not invoice_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=invoice_result["error"]
            )
        
        # Step 3: Update order record
        update_fields = {
            "invoice_no": invoice_result["invoice_no"],
            "invoice_file_to_byte": invoice_result["file_to_bytes"]
        }
        
        success = await teable_service.update_record(
            client, data.order_table_id, data.record_order_id, update_fields
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invoice created successfully but failed to update order record"
            )
        
        return InvoiceResponse(
            detail="Invoice created and order updated successfully",
            invoice_no=invoice_result["invoice_no"],
            file_name=invoice_result["file_name"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error generating invoice: {str(e)}"
        )
