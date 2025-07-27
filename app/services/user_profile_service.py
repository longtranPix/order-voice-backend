"""
User profile service for getting and updating user information
"""
import json
import logging
import requests
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.schemas.user_profile import (
    GetMeResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UserProfileResponse
)


logger = logging.getLogger(__name__)

security = HTTPBearer()

# User table view ID for profile queries
USER_PROFILE_VIEW_ID = "viw6ye3dhnsRIJXAV4p"

def parse_datetime_to_gmt7(date_str):
    """Parse datetime string and convert to GMT+7 timezone"""
    if date_str:
        try:
            # Parse the datetime and convert to GMT+7
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Convert to GMT+7 timezone
            gmt_plus_7 = timezone(timedelta(hours=7))
            return dt.astimezone(gmt_plus_7)
        except:
            return None
    return None

async def get_current_user_profile(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current user from token
    Returns username if token is valid, raises HTTPException if not
    """
    try:
        token = credentials.credentials
        logger.info(f"token: {token}")
        # Get username by token from token list table
        profile = await get_profile_by_token(token)
        logger.info(f"Authenticated user {profile.get('username')} with token {token[:20]}...", profile)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or token not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

async def get_profile_by_token(token: str) -> dict:
    """Get username by token from token list table"""
    try:
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Query token list table to find username by token
        token_list_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "viewId": "viw6ye3dhnsRIJXAV4p",
                "filterSet": [
                    {"fieldId": "access_token", "operator": "is", "value": token}
                ]
            })
        }
        
        response = requests.get(token_list_url, headers=headers, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to get token info: {response.text}")
            return ""
        
        data = response.json()
        records = data.get("records", [])
        
        if not records:
            logger.warning(f"No user found for token: {token[:20]}...")
            return None

        # Get username from the first matching record
        username = records[0].get("fields", {}).get("username", "")
        if username:
            logger.info(f"Found username {username} for token")

            # Now get the full user profile from user table
            # user_profile_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
            # user_params = {
            #     "fieldKeyType": "dbFieldName",
            #     "viewId": USER_PROFILE_VIEW_ID,
            #     "filter": json.dumps({
            #         "conjunction": "and",
            #         "filterSet": [
            #             {"fieldId": "username", "operator": "is", "value": username}
            #         ]
            #     })
            # }

            # user_response = requests.get(user_profile_url, headers=headers, params=user_params)
            # if user_response.status_code != 200:
            #     logger.error(f"Failed to get user profile: {user_response.text}")
            #     return None

            # user_data = user_response.json()
            # user_records = user_data.get("records", [])

            # if not user_records:
            #     logger.warning(f"No user profile found for username: {username}")
            #     return None

            # # Return the full user profile with id
            # user_record = user_records[0]
            profile_data = records[0].get("fields", {})
            profile_data["id"] = records[0].get("id")  # Add record ID
            return profile_data
        else:
            logger.warning(f"Username field not found in token record")
            return None
            
    except Exception as e:
        logger.error(f"Error getting username by token: {str(e)}")
        return None

async def get_current_user_profile_by_id(user_id: str) -> UserProfileResponse:
    """Get user profile by user ID"""
    try:
        # Prepare the API URL
        api_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record/{user_id}"

        # Prepare headers
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Add fieldKeyType parameter
        params = {
            "fieldKeyType": "dbFieldName"
        }

        logger.info(f"Getting user profile for user ID: {user_id}")

        # Make the API call
        response = requests.get(api_url, headers=headers, params=params)

        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Teable API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lỗi khi lấy thông tin người dùng: {response.status_code}"
            )

        # Parse the response
        user_record = response.json()
        fields = user_record.get("fields", {})

        # Create the user profile response with GMT+7 conversion
        user_profile = UserProfileResponse(
            username=fields.get("username", ""),
            business_name=fields.get("business_name", ""),
            current_plan_name=fields.get("current_plan_name"),
            last_login=parse_datetime_to_gmt7(fields.get("last_login")),
            time_expired=parse_datetime_to_gmt7(fields.get("time_expired"))
        )

        return user_profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user_profile_by_id: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )

async def update_user_profile_by_authorization(update_data: UpdateProfileRequest, current_user_id) -> UpdateProfileResponse:
    """
    Update user profile information by Authorization header with Teable token
    """
    logger.info(f"Updating user profile for user ID: {current_user_id}")
    try:
        # Prepare the API URL for update
        api_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record/{current_user_id}"
        
        # Prepare headers
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Build update payload - only include fields that have values
        update_fields = {}
        
        # Only add fields that are not None
        if update_data.business_name is not None:
            update_fields["business_name"] = update_data.business_name
        
        # If no fields to update, get current profile and return it
        if not update_fields:
            # Get current user profile
            current_profile = await get_current_user_profile_by_id(current_user_id)
            return UpdateProfileResponse(
                status="success",
                message="Không có thông tin nào được cập nhật",
                data=current_profile
            )
        
        # Prepare update payload
        payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "record": {
                "fields": update_fields
            }
        }
        
        logger.info(f"Updating user profile for record ID: {current_user_id}")
        logger.info(f"Update fields: {update_fields}")
        
        # Make the API call
        response = requests.patch(api_url, headers=headers, data=json.dumps(payload))
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Teable API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lỗi khi cập nhật thông tin: {response.status_code}"
            )
        
        logger.info(f"Successfully updated user profile for record ID: {current_user_id}")

        # Get updated user profile
        updated_profile = await get_current_user_profile_by_id(current_user_id)

        return UpdateProfileResponse(
            status="success",
            message="Cập nhật thông tin thành công",
            data=updated_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_user_profile_by_token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )

async def get_current_user_from_token(authorization_header: str) -> str:
    """
    Extract access_token from Authorization header
    """
    if not authorization_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu token xác thực"
        )
    
    if not authorization_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token xác thực không hợp lệ"
        )
    
    access_token = authorization_header.replace("Bearer ", "")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token xác thực trống"
        )
    
    return access_token
