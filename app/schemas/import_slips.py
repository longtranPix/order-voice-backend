"""
Import slip schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import List

class ImportSlipDetailItem(BaseModel):
    """Schema for import slip detail item"""
    product_id: str  # ID of product from product table
    unit_conversions_id: str  # ID of unit conversion from unit conversions table
    quantity: float
    unit_price: float
    vat: float = 10.0  # Default VAT 10%

class CreateImportSlipRequest(BaseModel):
    """Schema for creating import slip"""
    supplier_id: str  # ID of supplier from supplier table
    import_type: str = "Nhập mua"  # Default import type
    import_slip_details: List[ImportSlipDetailItem]

class ImportSlipResponse(BaseModel):
    """Schema for import slip response"""
    status: str
    detail: str
    import_slip_id: str
    import_slip_code: str
    import_slip_details_ids: List[str]
    total_items: int
    total_amount: float
