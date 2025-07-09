"""
Unit conversion schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import List, Optional

class CreateUnitConversionRequest(BaseModel):
    """Schema for creating unit conversion"""
    name_unit: str
    conversion_factor: float
    unit_default: str
    price: float = 0
    vat: float = 10.0  # VAT rate for this unit conversion

class UnitConversionResponse(BaseModel):
    """Schema for unit conversion response"""
    unit_conversion_id: str
    name_unit: str
    conversion_factor: float
    unit_default: str
    price: float
    vat: float  # VAT rate for this unit conversion

class CreateUnitConversionResponse(BaseModel):
    """Schema for create unit conversion response"""
    status: str
    detail: str
    unit_conversion_id: str
    unit_conversion_data: UnitConversionResponse

class GetUnitConversionsResponse(BaseModel):
    """Schema for get unit conversions response"""
    status: str
    detail: str
    unit_conversions: List[UnitConversionResponse]
    total_found: int
