import json
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.orders import CreateOrderRequest
from app.services.order_service import create_order_service
from app.utils.jwt_auth import get_current_user
from app.utils.auth_utils import handle_teable_api_call
from app.core.config import settings

router = APIRouter()

@router.post("/create-order")
async def create_order(
    data: CreateOrderRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create new order endpoint - Protected by authentication"""
    try:
        return await create_order_service(data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi tạo đơn hàng: {str(e)}"
        )

# @router.get("/orders")
# async def get_orders(current_user: dict = Depends(get_current_active_user)):
#     """Get user's orders - Protected by authentication"""
#     try:
#         username = current_user.get("sub")
#         # Implementation to fetch user's orders
#         return {
#             "status": "success",
#             "message": f"Orders for user {username}",
#             "orders": []
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Lỗi lấy danh sách đơn hàng: {str(e)}"
#         )
