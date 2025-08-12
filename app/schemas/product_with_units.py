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
    price: Optional[float] = 0
    vat: Optional[float] = 10.0

class CreateProductWithUnitsRequest(BaseModel):
    """Schema for creating product with inline unit conversions"""
    product_name: str
    unit_conversions: List[UnitConversionData]
    brand_id: Optional[str] = None
    attributes_ids: Optional[List[str]] = None

class CreatedUnitConversionResponse(BaseModel):
    """Schema for created unit conversion response"""
    unit_conversion_id: str
    name_unit: str
    conversion_factor: float
    unit_default: str
    price: float
    vat: float

class ProductWithUnitsResponse(BaseModel):
    """Schema for product with units response"""
    product_id: str
    product_name: str
    unit_conversions: Optional[List[CreatedUnitConversionResponse]] = None
    brand_id: Optional[str] = None
    # catalogs_id: Optional[List[str]] = None
    # product_line_id: Optional[str] = None
    attributes_ids: Optional[List[str]] = None
    # Fields set when only one unit conversion
    unit_default: Optional[str] = None
    price: Optional[float] = None
    vat_rate: Optional[float] = None

class CreateProductWithUnitsResponse(BaseModel):
    """Schema for create product with units response"""
    status: str
    detail: str
    product_id: str
    # created_unit_conversion_ids: Optional[List[str]] = None
    # created_unit_conversions: Optional[List[CreatedUnitConversionResponse]] = None
    product_data: ProductWithUnitsResponse
