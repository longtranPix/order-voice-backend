"""
Customer schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import List, Optional

class CreateCustomerRequest(BaseModel):
    """Schema for creating customer"""
    phone_number: str
    fullname: str
    address: Optional[str] = None
    email: Optional[str] = None

class CustomerResponse(BaseModel):
    """Schema for customer response"""
    customer_id: str
    phone_number: str
    fullname: str
    address: Optional[str] = None
    email: Optional[str] = None

class CreateCustomerResponse(BaseModel):
    """Schema for create customer response"""
    status: str
    detail: str
    customer_id: str
    customer_data: CustomerResponse

class FindCustomersResponse(BaseModel):
    """Schema for find customers response"""
    status: str
    detail: str
    customers: List[CustomerResponse]
    total_found: int
