"""
Unit conversion routes
"""
from fastapi import APIRouter, Depends
from app.schemas.unit_conversions import CreateUnitConversionRequest, CreateUnitConversionResponse, GetUnitConversionsResponse
from app.services.unit_conversion_service import create_unit_conversion_service, get_unit_conversions_service
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/create-unit-conversion", response_model=CreateUnitConversionResponse)
async def create_unit_conversion(
    data: CreateUnitConversionRequest, 
    current_user: str = Depends(get_current_user)
):
    """Create new unit conversion endpoint"""
    return await create_unit_conversion_service(data, current_user)

@router.get("/list", response_model=GetUnitConversionsResponse)
async def get_unit_conversions(
    current_user: str = Depends(get_current_user)
):
    """Get all unit conversions endpoint"""
    return await get_unit_conversions_service(current_user)
