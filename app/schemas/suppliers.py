from pydantic import BaseModel

class CreateSupplierRequest(BaseModel):
    supplier_name: str
    address: str

class CreateSupplierResponse(BaseModel):
    status: str
    detail: str
    supplier_id: str
    supplier_name: str
    address: str
