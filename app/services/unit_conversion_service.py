"""
Unit conversion service for managing unit conversion records
"""
import json
import logging
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.teable_service import handle_teable_api_call
from app.services.auth_service import get_user_table_info
from app.schemas.unit_conversions import CreateUnitConversionRequest, CreateUnitConversionResponse, GetUnitConversionsResponse, UnitConversionResponse

logger = logging.getLogger(__name__)



async def create_unit_conversion_service(data: CreateUnitConversionRequest, current_user: str) -> CreateUnitConversionResponse:
    """Create new unit conversion record"""
    try:
        # Get user table information
        user_info = await get_user_table_info(current_user)
        
        unit_conversion_table_id = user_info.get("table_unit_conversion_id")
        access_token = user_info.get("access_token")
        
        if not all([unit_conversion_table_id, access_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu thông tin bảng đơn vị tính chuyển đổi"
            )
        
        # Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Create unit conversion record
        unit_conversion_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": {
                    "name_unit": data.name_unit,
                    "conversion_factor": data.conversion_factor,
                    "unit_default": data.unit_default,
                    "price": data.price,
                    "vat_rate": data.vat
                }
            }]
        }
        
        unit_conversion_url = f"{settings.TEABLE_BASE_URL}/table/{unit_conversion_table_id}/record"
        result = handle_teable_api_call("POST", unit_conversion_url, data=json.dumps(unit_conversion_payload), headers=headers)
        
        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo đơn vị tính: {result.get('error', 'Unknown error')}"
            )
        
        # Get created unit conversion info
        unit_conversion_record = result.get("data", {}).get("records", [{}])[0]
        unit_conversion_id = unit_conversion_record.get("id", "")
        unit_conversion_fields = unit_conversion_record.get("fields", {})
        
        logger.info(f"Successfully created unit conversion {unit_conversion_id} for user {current_user}")
        
        return CreateUnitConversionResponse(
            status="success",
            detail="Đơn vị tính đã được tạo thành công",
            unit_conversion_id=unit_conversion_id,
            unit_conversion_data=UnitConversionResponse(
                unit_conversion_id=unit_conversion_id,
                name_unit=unit_conversion_fields.get("name_unit", ""),
                conversion_factor=unit_conversion_fields.get("conversion_factor", 0),
                unit_default=unit_conversion_fields.get("unit_default", ""),
                price=unit_conversion_fields.get("price", 0),
                vat=unit_conversion_fields.get("vat_rate", 10.0)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating unit conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo đơn vị tính: {str(e)}"
        )

async def get_unit_conversions_service(current_user: str) -> GetUnitConversionsResponse:
    """Get all unit conversions for the user"""
    try:
        # Get user table information
        user_info = await get_user_table_info(current_user)
        
        unit_conversion_table_id = user_info.get("table_unit_conversion_id")
        access_token = user_info.get("access_token")
        
        if not all([unit_conversion_table_id, access_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu thông tin bảng đơn vị tính chuyển đổi"
            )
        
        # Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Get all unit conversions
        unit_conversions_url = f"{settings.TEABLE_BASE_URL}/table/{unit_conversion_table_id}/record"
        params = {
            "fieldKeyType": "dbFieldName"
        }
        
        result = handle_teable_api_call("GET", unit_conversions_url, params=params, headers=headers)
        
        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể lấy danh sách đơn vị tính: {result.get('error', 'Unknown error')}"
            )
        
        # Process results
        records = result.get("data", {}).get("records", [])
        unit_conversions = []
        
        for record in records:
            unit_conversion_id = record.get("id", "")
            fields = record.get("fields", {})
            
            unit_conversions.append(UnitConversionResponse(
                unit_conversion_id=unit_conversion_id,
                name_unit=fields.get("name_unit", ""),
                conversion_factor=fields.get("conversion_factor", 0),
                unit_default=fields.get("unit_default", ""),
                price=fields.get("price", 0),
                vat=fields.get("vat_rate", 10.0)
            ))
        
        logger.info(f"Retrieved {len(unit_conversions)} unit conversions for user {current_user}")
        
        return GetUnitConversionsResponse(
            status="success",
            detail=f"Tìm thấy {len(unit_conversions)} đơn vị tính",
            unit_conversions=unit_conversions,
            total_found=len(unit_conversions)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unit conversions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi lấy danh sách đơn vị tính: {str(e)}"
        )
