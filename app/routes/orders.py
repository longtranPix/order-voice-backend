from fastapi import APIRouter, Depends
from app.schemas.orders import CreateOrderRequest, CreateOrderResponse
from app.services.order_service import create_order_service
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(data: CreateOrderRequest, current_user: str = Depends(get_current_user)):
    """
    Create new order endpoint with automatic delivery note creation
    
    **Request Body:**
    ```json
    {
        "customer_id": "customer_record_id",
        "order_details": [
            {
                "product_id": "product_record_id",
                "unit_conversions_id": "unit_conversion_record_id",
                "unit_price": 100000,
                "quantity": 5,
                "vat": 10
            }
        ],
        "delivery_type": "Xuất bán",
        "payment_method": "Tiền mặt"
    }
    ```
    
    **Payment Methods Available:**
    - "Tiền mặt" (Cash)
    - "Chuyển khoản" (Bank Transfer)
    - "Thẻ tín dụng" (Credit Card)
    - "Ví điện tử" (E-wallet)
    - "Séc" (Check)
    
    **Response:**
    ```json
    {
        "status": "success",
        "detail": "Đơn hàng và phiếu xuất đã được tạo thành công",
        "order_id": "order_record_id",
        "order_code": "ORD001",
        "delivery_note_id": "delivery_note_record_id",
        "delivery_note_code": "DN001",
        "customer_id": "customer_record_id",
        "total_items": 1,
        "total_temp": 500000,
        "total_vat": 50000,
        "total_after_vat": 550000
    }
    ```
    """
    # Pass the current user to the service for user-specific operations
    return await create_order_service(data, current_user)
