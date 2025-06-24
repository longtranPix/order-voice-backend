from pydantic import BaseModel, field_validator
from typing import Dict, Any

class InvoiceRequest(BaseModel):
    """Schema for invoice generation request."""
    username: str
    order_table_id: str
    record_order_id: str
    invoice_payload: Dict[str, Any]

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Username cannot be empty')
        return v.strip()

    @field_validator('invoice_payload')
    @classmethod
    def validate_invoice_payload(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Invoice payload must be a dictionary')
        if 'generalInvoiceInfo' not in v:
            raise ValueError('Invoice payload must contain generalInvoiceInfo')
        if 'templateCode' not in v.get('generalInvoiceInfo', {}):
            raise ValueError('generalInvoiceInfo must contain templateCode')
        return v

class InvoiceResponse(BaseModel):
    """Schema for invoice generation response."""
    detail: str
    invoice_no: str
    file_name: str
