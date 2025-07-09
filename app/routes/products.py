"""
Product routes
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.schemas.products import (
    CreateProductRequest,
    CreateProductResponse,
    FindProductsResponse,
    CreateProductWithUnitsRequest,
    CreateProductWithUnitsResponse
)
from app.services.product_service import (
    create_product_service,
    find_products_by_name_service,
    create_product_with_units_service
)
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/create-product", response_model=CreateProductResponse)
async def create_product(
    data: CreateProductRequest, 
    current_user: str = Depends(get_current_user)
):
    """Create new product endpoint"""
    return await create_product_service(data, current_user)

@router.get("/find-by-name", response_model=FindProductsResponse)
async def find_products_by_name(
    name: str = Query(..., description="Product name to search for"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, description="Maximum number of results"),
    current_user: str = Depends(get_current_user)
):
    """Find products by name endpoint"""
    return await find_products_by_name_service(name, current_user, category, limit)

@router.post("/create-product-with-units", response_model=CreateProductWithUnitsResponse)
async def create_product_with_units(
    data: CreateProductWithUnitsRequest,
    current_user: str = Depends(get_current_user)
):
    """Create product with inline unit conversions endpoint"""
    return await create_product_with_units_service(data, current_user)
