"""
Product service for managing product records
"""
import json
import logging
from typing import List
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.teable_service import handle_teable_api_call
from app.services.auth_service import get_user_table_info
from app.services.plan_status_service import reduce_credit_value_on_order_complete
from app.schemas.products import (
    CreateProductRequest,
    CreateProductResponse,
    FindProductsResponse,
    ProductResponse,
    CreateProductWithUnitsRequest,
    CreateProductWithUnitsResponse,
    CreatedUnitConversionResponse
)

logger = logging.getLogger(__name__)



async def create_product_service(data: CreateProductRequest, current_user: str) -> CreateProductResponse:
    """Create new product record"""
    try:
        # Get user table information
        user_info = await get_user_table_info(current_user)
        
        product_table_id = user_info.get("table_product_id")
        access_token = user_info.get("access_token")
        
        if not all([product_table_id, access_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu thông tin bảng sản phẩm"
            )
        
        # Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Create product record
        product_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": {
                    "product_name": data.product_name,
                    "unit_conversions": data.unit_conversions
                }
            }]
        }
        
        product_url = f"{settings.TEABLE_BASE_URL}/table/{product_table_id}/record"
        result = handle_teable_api_call("POST", product_url, data=json.dumps(product_payload), headers=headers)
        
        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo sản phẩm: {result.get('error', 'Unknown error')}"
            )
        
        # Get created product info
        product_record = result.get("data", {}).get("records", [{}])[0]
        product_id = product_record.get("id", "")
        product_fields = product_record.get("fields", {})
        
        # Reduce credit value after successful product creation
        credit_reduced = await reduce_credit_value_on_order_complete(current_user)
        if credit_reduced:
            logger.info(f"Successfully reduced credit value for user {current_user} after product creation")
        else:
            logger.warning(f"Failed to reduce credit value for user {current_user}, but product was created successfully")

        logger.info(f"Successfully created product {product_id} for user {current_user}")

        return CreateProductResponse(
            status="success",
            detail="Sản phẩm đã được tạo thành công",
            product_id=product_id,
            product_data=ProductResponse(
                product_id=product_id,
                product_name=product_fields.get("product_name", ""),
                unit_conversions=product_fields.get("unit_conversions", [])
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo sản phẩm: {str(e)}"
        )

async def find_products_by_name_service(name: str, current_user: str, category: str = None, limit: int = 10) -> FindProductsResponse:
    """Find products by name with partial matching"""
    try:
        # Get user table information
        user_info = await get_user_table_info(current_user)
        
        product_table_id = user_info.get("table_product_id")
        access_token = user_info.get("access_token")
        
        if not all([product_table_id, access_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu thông tin bảng sản phẩm"
            )
        
        # Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Build filter conditions
        filter_conditions = [
            {"fieldId": "product_name", "operator": "contains", "value": name}
        ]
        
        if category:
            filter_conditions.append(
                {"fieldId": "category", "operator": "is", "value": category}
            )
        
        # Search products by name
        search_url = f"{settings.TEABLE_BASE_URL}/table/{product_table_id}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": filter_conditions
            }),
            "take": limit
        }
        
        result = handle_teable_api_call("GET", search_url, params=params, headers=headers)
        
        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tìm kiếm sản phẩm: {result.get('error', 'Unknown error')}"
            )
        
        # Process search results
        records = result.get("data", {}).get("records", [])
        products = []
        
        for record in records:
            product_id = record.get("id", "")
            fields = record.get("fields", {})
            
            products.append(ProductResponse(
                product_id=product_id,
                product_name=fields.get("product_name", ""),
                unit_conversions=fields.get("unit_conversions", [])
            ))
        
        logger.info(f"Found {len(products)} products matching '{name}' for user {current_user}")
        
        return FindProductsResponse(
            status="success",
            detail=f"Tìm thấy {len(products)} sản phẩm",
            products=products,
            total_found=len(products)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tìm kiếm sản phẩm: {str(e)}"
        )

async def create_product_with_units_service(data: CreateProductWithUnitsRequest, current_user: str) -> CreateProductWithUnitsResponse:
    """Create product with inline unit conversion creation"""
    try:
        # Get user table information
        user_info = await get_user_table_info(current_user)

        product_table_id = user_info.get("table_product_id")
        unit_conversion_table_id = user_info.get("table_unit_conversions_id")
        access_token = user_info.get("access_token")

        if not all([product_table_id, unit_conversion_table_id, access_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu thông tin bảng sản phẩm hoặc đơn vị tính"
            )

        # Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        created_unit_conversions = []
        created_unit_conversion_ids = []

        # Step 1: Create all unit conversion records first
        for unit_data in data.unit_conversions:
            unit_conversion_payload = {
                "fieldKeyType": "dbFieldName",
                "typecast": True,
                "records": [{
                    "fields": {
                        "name_unit": unit_data.name_unit,
                        "conversion_factor": unit_data.conversion_factor,
                        "unit_default": unit_data.unit_default,
                        "price": getattr(unit_data, 'price', 0),
                        "vat_rate": getattr(unit_data, 'vat', 10.0)
                    }
                }]
            }

            unit_conversion_url = f"{settings.TEABLE_BASE_URL}/table/{unit_conversion_table_id}/record"
            result = handle_teable_api_call("POST", unit_conversion_url, data=json.dumps(unit_conversion_payload), headers=headers)

            if not result["success"]:
                # Rollback: Delete any previously created unit conversions
                await rollback_unit_conversions(created_unit_conversion_ids, unit_conversion_table_id, headers)
                raise HTTPException(
                    status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                    detail=f"Không thể tạo đơn vị tính '{unit_data.name_unit}': {result.get('error', 'Unknown error')}"
                )

            # Get created unit conversion info
            unit_conversion_record = result.get("data", {}).get("records", [{}])[0]
            unit_conversion_id = unit_conversion_record.get("id", "")
            unit_conversion_fields = unit_conversion_record.get("fields", {})

            created_unit_conversion_ids.append(unit_conversion_id)
            created_unit_conversions.append(CreatedUnitConversionResponse(
                unit_conversion_id=unit_conversion_id,
                name_unit=unit_conversion_fields.get("name_unit", ""),
                conversion_factor=unit_conversion_fields.get("conversion_factor", 0),
                unit_default=unit_conversion_fields.get("unit_default", ""),
                price=unit_conversion_fields.get("price", 0),
                vat=unit_conversion_fields.get("vat_rate", 10.0)
            ))

        # Step 2: Create product record with links to unit conversions
        product_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": {
                    "product_name": data.product_name,
                    "unit_conversions": created_unit_conversion_ids,
                    "brand": data.brand_id
                }
            }]
        }

        product_url = f"{settings.TEABLE_BASE_URL}/table/{product_table_id}/record"
        result = handle_teable_api_call("POST", product_url, data=json.dumps(product_payload), headers=headers)

        if not result["success"]:
            # Rollback: Delete all created unit conversions
            await rollback_unit_conversions(created_unit_conversion_ids, unit_conversion_table_id, headers)
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo sản phẩm: {result.get('error', 'Unknown error')}"
            )

        # Get created product info
        product_record = result.get("data", {}).get("records", [{}])[0]
        product_id = product_record.get("id", "")
        product_fields = product_record.get("fields", {})

        # Reduce credit value after successful product with units creation
        credit_reduced = await reduce_credit_value_on_order_complete(current_user)
        if credit_reduced:
            logger.info(f"Successfully reduced credit value for user {current_user} after product with units creation")
        else:
            logger.warning(f"Failed to reduce credit value for user {current_user}, but product with units was created successfully")

        logger.info(f"Successfully created product {product_id} with {len(created_unit_conversions)} unit conversions for user {current_user}")

        return CreateProductWithUnitsResponse(
            status="success",
            detail=f"Sản phẩm và {len(created_unit_conversions)} đơn vị tính đã được tạo thành công",
            product_id=product_id,
            product_data=ProductResponse(
                product_id=product_id,
                product_name=product_fields.get("product_name", ""),
                unit_conversions=created_unit_conversion_ids
            ),
            created_unit_conversions=created_unit_conversions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product with units: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo sản phẩm với đơn vị tính: {str(e)}"
        )

async def rollback_unit_conversions(unit_conversion_ids: List[str], unit_conversion_table_id: str, headers: dict):
    """Rollback created unit conversions in case of failure"""
    try:
        for unit_conversion_id in unit_conversion_ids:
            delete_url = f"{settings.TEABLE_BASE_URL}/table/{unit_conversion_table_id}/record/{unit_conversion_id}"
            handle_teable_api_call("DELETE", delete_url, headers=headers)
            logger.info(f"Rolled back unit conversion {unit_conversion_id}")
    except Exception as e:
        logger.error(f"Error during rollback: {str(e)}")
        # Continue with rollback even if some deletions fail
