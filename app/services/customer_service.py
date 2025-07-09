"""
Customer service for managing customer records
"""
import json
import logging
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.teable_service import handle_teable_api_call
from app.services.auth_service import get_user_table_info
from app.schemas.customers import CreateCustomerRequest, CreateCustomerResponse, FindCustomersResponse, CustomerResponse


logger = logging.getLogger(__name__)

async def create_customer_service(data: CreateCustomerRequest, current_user: str) -> CreateCustomerResponse:
    """Create new customer record"""
    try:
        # Get user table information
        user_info = await get_user_table_info(current_user)
        
        customer_table_id = user_info.get("table_customer_id")
        access_token = user_info.get("access_token")
        
        if not all([customer_table_id, access_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu thông tin bảng khách hàng"
            )
        
        # Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Create customer record
        customer_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": {
                    "phone_number": data.phone_number,
                    "fullname": data.fullname,
                    "address": data.address or "",
                    "email": data.email or ""
                }
            }]
        }
        
        customer_url = f"{settings.TEABLE_BASE_URL}/table/{customer_table_id}/record"
        result = handle_teable_api_call("POST", customer_url, data=json.dumps(customer_payload), headers=headers)
        
        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo khách hàng: {result.get('error', 'Unknown error')}"
            )
        
        # Get created customer info
        customer_record = result.get("data", {}).get("records", [{}])[0]
        customer_id = customer_record.get("id", "")
        customer_fields = customer_record.get("fields", {})
        
        logger.info(f"Successfully created customer {customer_id} for user {current_user}")
        
        return CreateCustomerResponse(
            status="success",
            detail="Khách hàng đã được tạo thành công",
            customer_id=customer_id,
            customer_data=CustomerResponse(
                customer_id=customer_id,
                phone_number=customer_fields.get("phone_number", ""),
                fullname=customer_fields.get("fullname", ""),
                address=customer_fields.get("address", ""),
                email=customer_fields.get("email", "")
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo khách hàng: {str(e)}"
        )

async def find_customers_by_name_service(name: str, current_user: str, limit: int = 10) -> FindCustomersResponse:
    """Find customers by name with partial matching"""
    try:
        # Get user table information
        user_info = await get_user_table_info(current_user)
        
        customer_table_id = user_info.get("table_customer_id")
        access_token = user_info.get("access_token")
        
        if not all([customer_table_id, access_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu thông tin bảng khách hàng"
            )
        
        # Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Search customers by name
        search_url = f"{settings.TEABLE_BASE_URL}/table/{customer_table_id}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "fullname", "operator": "contains", "value": name}
                ]
            }),
            "take": limit
        }
        
        result = handle_teable_api_call("GET", search_url, params=params, headers=headers)
        
        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tìm kiếm khách hàng: {result.get('error', 'Unknown error')}"
            )
        
        # Process search results
        records = result.get("data", {}).get("records", [])
        customers = []
        
        for record in records:
            customer_id = record.get("id", "")
            fields = record.get("fields", {})
            
            customers.append(CustomerResponse(
                customer_id=customer_id,
                phone_number=fields.get("phone_number", ""),
                fullname=fields.get("fullname", ""),
                address=fields.get("address", ""),
                email=fields.get("email", "")
            ))
        
        logger.info(f"Found {len(customers)} customers matching '{name}' for user {current_user}")
        
        return FindCustomersResponse(
            status="success",
            detail=f"Tìm thấy {len(customers)} khách hàng",
            customers=customers,
            total_found=len(customers)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding customers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tìm kiếm khách hàng: {str(e)}"
        )
