"""
Delivery note schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import List, Optional

class DeliveryNoteDetailItem(BaseModel):
    """Schema for delivery note detail item"""
    product_id: str  # ID of product from product table
    unit_conversions_id: Optional[str] = None  # ID of unit conversion from unit conversions table
    quantity: float
    unit_price: float
    vat: float = 10.0  # Default VAT 10%

class CreateDeliveryNoteRequest(BaseModel):
    """Schema for creating delivery note"""
    order_id: str  # ID of the order this delivery note fulfills
    customer_id: str  # ID of customer from customer table
    delivery_type: str = "Xuất bán"  # Default delivery type
    delivery_note_details: List[DeliveryNoteDetailItem]
    notes: Optional[str] = None  # Optional notes

class DeliveryNoteResponse(BaseModel):
    """Schema for delivery note response"""
    status: str
    detail: str
    delivery_note_id: str
    delivery_note_code: str
    delivery_note_details_ids: List[str]
    order_id: str
    customer_id: str
    total_items: int
    total_amount: float
