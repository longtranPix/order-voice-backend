"""
Customer routes
"""
from fastapi import APIRouter, Depends, Query
from app.schemas.customers import CreateCustomerRequest, CreateCustomerResponse, FindCustomersResponse
from app.services.customer_service import create_customer_service, find_customers_by_name_service
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/create-customer", response_model=CreateCustomerResponse)
async def create_customer(
    data: CreateCustomerRequest, 
    current_user: str = Depends(get_current_user)
):
    """Create new customer endpoint"""
    return await create_customer_service(data, current_user)

@router.get("/find-by-name", response_model=FindCustomersResponse)
async def find_customers_by_name(
    name: str = Query(..., description="Customer name to search for"),
    limit: int = Query(10, description="Maximum number of results"),
    current_user: str = Depends(get_current_user)
):
    """Find customers by name endpoint"""
    return await find_customers_by_name_service(name, current_user, limit)
