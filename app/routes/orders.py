from fastapi import APIRouter, Depends
from app.schemas.orders import CreateOrderRequest, CreateOrderResponse
from app.services.order_service import create_order_service
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(data: CreateOrderRequest, current_user: str = Depends(get_current_user)):
    """Create new order endpoint with automatic delivery note creation"""
    # Pass the current user to the service for user-specific operations
    return await create_order_service(data, current_user)
