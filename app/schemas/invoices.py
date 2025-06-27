from pydantic import BaseModel
from typing import Dict, Any

class InvoiceRequest(BaseModel):
    username: str
    order_table_id: str
    record_order_id: str
    field_attachment_id: str
    invoice_payload: Dict[str, Any]  # Will be automatically populated with invoice config
