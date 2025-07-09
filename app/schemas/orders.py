from pydantic import BaseModel
from typing import List

class OrderDetail(BaseModel):
    product_id: str  # Changed from product_name to product_id
    unit_conversions_id: str  # Added unit conversions ID
    unit_price: float
    quantity: int
    vat: float

class CreateOrderRequest(BaseModel):
    customer_id: str  # Changed from customer_name to customer_id
    order_details: List[OrderDetail]
    delivery_type: str = "Xuất bán"  # Default delivery type

class CreateOrderResponse(BaseModel):
    """Schema for order creation response"""
    status: str
    detail: str
    order_id: str
    order_code: str
    delivery_note_id: str
    delivery_note_code: str
    customer_id: str
    total_items: int
    total_temp: float
    total_vat: float
    total_after_vat: float
