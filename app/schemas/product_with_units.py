"""
Product with units schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import List, Optional

class UnitConversionData(BaseModel):
    """Schema for unit conversion data in product creation"""
    name_unit: str
    conversion_factor: float
    unit_default: str

class CreateProductWithUnitsRequest(BaseModel):
    """Schema for creating product with inline unit conversions"""
    product_name: str
    unit_price: float
    vat_rate: float = 10.0
    unit_conversions: List[UnitConversionData]

class CreatedUnitConversionResponse(BaseModel):
    """Schema for created unit conversion response"""
    unit_conversion_id: str
    name_unit: str
    conversion_factor: float
    unit_default: str

class ProductWithUnitsResponse(BaseModel):
    """Schema for product with units response"""
    product_id: str
    product_name: str
    unit_price: float
    vat_rate: float
    unit_conversions: List[CreatedUnitConversionResponse]

class CreateProductWithUnitsResponse(BaseModel):
    """Schema for create product with units response"""
    status: str
    detail: str
    product_id: str
    created_unit_conversion_ids: List[str]
    product_data: ProductWithUnitsResponse
