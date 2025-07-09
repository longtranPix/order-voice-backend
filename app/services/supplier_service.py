import json
import logging
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.suppliers import CreateSupplierRequest, CreateSupplierResponse
from app.services.teable_service import handle_teable_api_call
from app.services.auth_service import get_user_table_info

logger = logging.getLogger(__name__)

async def create_supplier_service(data: CreateSupplierRequest, current_user: str) -> CreateSupplierResponse:
    """Create a new supplier"""
    try:
        logger.info(f"Creating supplier for user: {current_user}")
        
        # Step 1: Get user table information
        user_info = await get_user_table_info(current_user)
        supplier_table_id = user_info.get("table_supplier_id")
        access_token = user_info.get("access_token")
        
        if not supplier_table_id or not access_token:
            missing_fields = []
            if not supplier_table_id: missing_fields.append("table_supplier_id")
            if not access_token: missing_fields.append("access_token")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Thiếu thông tin bảng cần thiết: {', '.join(missing_fields)}"
            )
        
        # Step 2: Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Step 3: Create supplier record
        supplier_record = {
            "fields": {
                "supplier_name": data.supplier_name,
                "address": data.address
            }
        }
        
        supplier_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [supplier_record]
        }
        
        supplier_url = f"{settings.TEABLE_BASE_URL}/table/{supplier_table_id}/record"
        supplier_result = handle_teable_api_call("POST", supplier_url, data=json.dumps(supplier_payload), headers=headers)
        
        if not supplier_result["success"]:
            raise HTTPException(
                status_code=supplier_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo nhà cung cấp: {supplier_result.get('error', 'Unknown error')}"
            )
        
        # Get created supplier record
        supplier_records = supplier_result.get("data", {}).get("records", [])
        if not supplier_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể lấy thông tin nhà cung cấp đã tạo"
            )
        
        supplier_record_created = supplier_records[0]
        supplier_id = supplier_record_created.get("id", "")
        
        logger.info(f"Successfully created supplier {supplier_id} for user {current_user}")
        
        return CreateSupplierResponse(
            status="success",
            detail="Nhà cung cấp đã được tạo thành công",
            supplier_id=supplier_id,
            supplier_name=data.supplier_name,
            address=data.address
        )
        
    except HTTPException as e:
        logger.error(f"HTTP error in create_supplier_service: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in create_supplier_service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo nhà cung cấp: {str(e)}"
        )
