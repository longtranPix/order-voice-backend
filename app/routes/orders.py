from fastapi import APIRouter
from app.schemas.orders import CreateOrderRequest
from app.services.order_service import create_order_service

router = APIRouter()

@router.post("/create-order")
async def create_order(data: CreateOrderRequest):
    """Create new order endpoint"""
    return await create_order_service(data)
