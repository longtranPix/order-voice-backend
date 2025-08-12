"""
Product schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import List, Optional

class UnitConversionData(BaseModel):
    """Schema for unit conversion data in product creation"""
    name_unit: str
    conversion_factor: float
    unit_default: str
    price: float = 0
    vat: float = 10.0  # VAT rate for this unit conversion

class CreateProductRequest(BaseModel):
    """Schema for creating product"""
    product_name: str
    unit_conversions: List[str] = []  # List of unit conversion IDs


class ProductResponse(BaseModel):
    """Schema for product response"""
    product_id: str
    product_name: str
    unit_conversions: List[str] = []  # List of unit conversion IDs

class CreateProductResponse(BaseModel):
    """Schema for create product response"""
    status: str
    detail: str
    product_id: str
    product_data: ProductResponse

class FindProductsResponse(BaseModel):
    """Schema for find products response"""
    status: str
    detail: str
    products: List[ProductResponse]
    total_found: int

class CreateProductWithUnitsRequest(BaseModel):
    """Schema for creating product with inline unit conversions"""
    product_name: str
    unit_conversions: List[UnitConversionData]
    catalogs_id: List[str] = None
    product_line_id: str
    brand_id: str = None

class CreatedUnitConversionResponse(BaseModel):
    """Schema for created unit conversion in product response"""
    unit_conversion_id: str
    name_unit: str
    conversion_factor: float
    unit_default: str
    price: float
    vat: float  # VAT rate for this unit conversion

class CreateProductWithUnitsResponse(BaseModel):
    """Schema for create product with units response"""
    status: str
    detail: str
    product_id: str
    product_data: ProductResponse
    created_unit_conversions: List[CreatedUnitConversionResponse]
    brand_id: str = None
