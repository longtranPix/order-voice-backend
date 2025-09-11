"""
Plan status service for retrieving plan information
"""
import json
import logging
import requests
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.plan_status import PlanStatusResponse, GetPlanStatusResponse, PlanStatusFields, AccountInfo, SoInfo
from datetime import datetime

logger = logging.getLogger(__name__)

# Plan status table ID from the API endpoint


async def get_plan_status_service(current_user: dict) -> GetPlanStatusResponse:
    """
    Get plan status information from current user's current_plan
    """
    try:
        # Step 1: Get user's current_plan.id from user table with specific viewId
        username = current_user.get("username")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username not found in current user data"
            )
        
        # Get user info with viewId to get current_plan
        user_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        params = {
            "fieldKeyType": "dbFieldName",
            "viewId": "viwTORaGGJFEmR5jNxf",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [{"fieldId": "username", "operator": "is", "value": username}]
            })
        }
        
        logger.info(f"Getting user info for username: {username}")
        user_response = requests.get(user_url, headers=headers, params=params)
        
        if user_response.status_code != 200:
            logger.error(f"Failed to get user info: {user_response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể lấy thông tin người dùng"
            )
        
        user_data = user_response.json()
        user_records = user_data.get("records", [])
        
        if not user_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông tin người dùng"
            )
        
        user_fields = user_records[0].get("fields", {})
        current_plan = user_fields.get("current_plan")
        
        if not current_plan or not current_plan.get("id"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Người dùng chưa có plan hiện tại"
            )
        
        plan_status_id = current_plan.get("id")
        logger.info(f"Found current_plan.id: {plan_status_id} for user: {username}")
        
        # Step 2: Get plan status information using the plan_status_id
        api_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_PLAN_STATUS_TABLE_ID}/record/{plan_status_id}"
        
        params = {
            "fieldKeyType": "dbFieldName"
        }
        
        logger.info(f"Calling Teable API for plan status: {plan_status_id}")
        
        # Make the API call
        response = requests.get(api_url, headers=headers, params=params)
        
        # Check if the request was successful
        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy plan status với ID: {plan_status_id}"
            )
        elif response.status_code != 200:
            logger.error(f"Teable API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lỗi khi gọi API Teable: {response.status_code}"
            )
        
        # Parse the response
        data = response.json()
        logger.info(f"Successfully retrieved plan status for user: {username}")
        
        # Parse the fields
        fields_data = data.get("fields", {})
        
        # Parse nested objects
        so_info = None
        # if "So" in fields_data and fields_data["So"]:
        #     so_info = SoInfo(
        #         id=fields_data["So"].get("id", ""),
        #         title=fields_data["So"].get("title", "")
        #     )
        
        # account_info = None
        # if "Tai_khoan" in fields_data and fields_data["Tai_khoan"]:
        #     account_info = AccountInfo(
        #         id=fields_data["Tai_khoan"].get("id", ""),
        #         title=fields_data["Tai_khoan"].get("title", "")
        #     )
        
        # Parse datetime fields
        def parse_datetime(date_str):
            if date_str:
                try:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    return None
            return None
        
        # Create the fields object
        plan_fields = PlanStatusFields(
            started_time=parse_datetime(fields_data.get("started_time")),
            cycle=fields_data.get("cycle"),
            time_expired=parse_datetime(fields_data.get("time_expired")),
            status=fields_data.get("status"),
            credit_value=fields_data.get("credit_value"),
            # Tai_khoan=account_info,
            name_plan=fields_data.get("name_plan")
        )
        
        # Create the response object
        plan_response = PlanStatusResponse(
            fields=plan_fields,
            name=data.get("name", ""),
            id=data.get("id", ""),
            autoNumber=data.get("autoNumber", 0),
            createdTime=parse_datetime(data.get("createdTime")) or datetime.now(),
            lastModifiedTime=parse_datetime(data.get("lastModifiedTime")) or datetime.now(),
            createdBy=data.get("createdBy", ""),
            lastModifiedBy=data.get("lastModifiedBy", "")
        )
        
        return GetPlanStatusResponse(
            status="success",
            message="Lấy thông tin plan status thành công",
            data=plan_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_plan_status_service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )

async def reduce_credit_value_on_order_complete(username: str) -> bool:
    """
    Reduce credit_value by 1 when order is completed successfully
    """
    try:
        # Step 1: Get user's current_plan ID from user table
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Get user info with current_plan field
        user_table_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        user_params = {
            "fieldKeyType": "dbFieldName",
            "viewId": settings.TEABLE_USER_VIEW_ID,
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": username}
                ]
            })
        }

        logger.info(f"Getting user info for credit reduction: {username}")
        user_response = requests.get(user_table_url, headers=headers, params=user_params)

        if user_response.status_code != 200:
            logger.error(f"Failed to get user info: {user_response.status_code} - {user_response.text}")
            return False

        user_data = user_response.json()
        user_records = user_data.get("records", [])

        if not user_records:
            logger.warning(f"No user found for username: {username}")
            return False

        # Get current_plan field (link field to plan status table)
        user_fields = user_records[0].get("fields", {})
        current_plan_status_id = user_fields.get("current_plan").get("id")
        logger.info(f"Current plan status ID: {current_plan_status_id} for user: {username}")

        if not current_plan_status_id:
            logger.warning(f"No current_plan found for user: {username}")
            return False

        # Extract plan status ID from current_plan link field
        # if isinstance(current_plan, list) and len(current_plan) > 0:
        #     plan_status_id = current_plan[0]  # Link field returns array
        # elif isinstance(current_plan, str):
        #     plan_status_id = current_plan
        # else:
        #     logger.warning(f"Invalid current_plan format for user: {username}")
        #     return False

        # logger.info(f"Found plan status ID: {plan_status_id} for user: {username}")

        # Step 2: Get current credit_value from plan status table
        plan_status_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_PLAN_STATUS_TABLE_ID}/record/{current_plan_status_id}"
        plan_params = {"fieldKeyType": "dbFieldName"}

        plan_response = requests.get(plan_status_url, headers=headers, params=plan_params)

        if plan_response.status_code != 200:
            logger.error(f"Failed to get plan status: {plan_response.status_code} - {plan_response.text}")
            return False

        plan_data = plan_response.json()
        current_credit_value = plan_data.get("fields", {}).get("credit_value", 0)

        if current_credit_value <= 0:
            logger.warning(f"Insufficient credit value ({current_credit_value}) for user: {username}")
            return False

        # Step 3: Reduce credit_value by 1
        new_credit_value = current_credit_value - 1

        # Update plan status record
        update_payload = {
            "fieldKeyType": "dbFieldName",
            "record": {
                "fields": {
                    "credit_value": new_credit_value
                }
            }
        }

        update_response = requests.patch(
            plan_status_url,
            headers=headers,
            data=json.dumps(update_payload)
        )

        if update_response.status_code == 200:
            logger.info(f"Successfully reduced credit value from {current_credit_value} to {new_credit_value} for user: {username}")
            return True
        else:
            logger.error(f"Failed to update credit value: {update_response.status_code} - {update_response.text}")
            return False

    except Exception as e:
        logger.error(f"Error reducing credit value for user {username}: {str(e)}")
        return False
