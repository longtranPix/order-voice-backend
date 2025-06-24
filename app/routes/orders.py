import httpx
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import CreateOrderRequest, OrderResponse
from app.services import TeableService
from app.utils import get_http_client
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/create", response_model=OrderResponse)
async def create_order(
    data: CreateOrderRequest,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Create a new order with details."""
    try:
        teable_service = TeableService()
        
        result = await teable_service.create_order_records(
            client,
            data.order_table_id,
            data.detail_table_id,
            data.customer_name,
            data.order_details,
            data.invoice_state
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return OrderResponse(
            status="success",
            order=result["order"],
            total_temp=result["total_temp"],
            total_vat=result["total_vat"],
            total_after_vat=result["total_after_vat"],
            invoice_state=result["invoice_state"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unexpected error creating order: {str(e)}"
        )
