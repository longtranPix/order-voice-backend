from pydantic import BaseModel, field_validator
from typing import List

class OrderDetail(BaseModel):
    """Schema for individual order item details."""
    product_name: str
    unit_price: float
    quantity: int
    vat: float
    temp_total: float
    final_total: float

    @field_validator('product_name')
    @classmethod
    def validate_product_name(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Product name cannot be empty')
        return v.strip()

    @field_validator('unit_price', 'quantity', 'temp_total', 'final_total')
    @classmethod
    def validate_positive_numbers(cls, v):
        if v < 0:
            raise ValueError('Value must be positive')
        return v

    @field_validator('vat')
    @classmethod
    def validate_vat_range(cls, v):
        if v < 0 or v > 100:
            raise ValueError('VAT must be between 0 and 100')
        return v

class CreateOrderRequest(BaseModel):
    """Schema for creating a new order."""
    customer_name: str
    invoice_state: bool
    order_details: List[OrderDetail]
    order_table_id: str
    detail_table_id: str

    @field_validator('customer_name')
    @classmethod
    def validate_customer_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Customer name must be at least 2 characters')
        return v.strip()

    @field_validator('order_details')
    @classmethod
    def validate_order_details(cls, v):
        if not v:
            raise ValueError('Order must contain at least one item')
        return v

class OrderResponse(BaseModel):
    """Schema for order creation response."""
    status: str
    order: dict
    total_temp: float
    total_vat: float
    total_after_vat: float
    invoice_state: bool
