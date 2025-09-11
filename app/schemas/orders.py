from pydantic import BaseModel
from typing import List, Optional

class OrderDetail(BaseModel):
    product_name: str
    unit_price: float
    quantity: int
    vat_rate: float

class CreateOrderRequest(BaseModel):
    order_code: Optional[str] = None
    customer_name: Optional[str] = None
    payment_method: Optional[str] = None  # "Chuyển khoản" or "Tiền mặt"
    order_details: List[OrderDetail]
