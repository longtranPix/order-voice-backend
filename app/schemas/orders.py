from pydantic import BaseModel
from typing import List

class OrderDetail(BaseModel):
    product_name: str
    unit_price: float
    quantity: int
    vat: float
    temp_total: float
    final_total: float

class CreateOrderRequest(BaseModel):
    customer_name: str
    order_details: List[OrderDetail]
    order_table_id: str
    detail_table_id: str
