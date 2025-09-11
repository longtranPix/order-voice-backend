"""
User profile service for getting and updating user information
"""
from fastapi import HTTPException
from app.schemas.profile import UserProfileResponse
from app.utils.auth_utils import get_profile_by_token, parse_datetime_to_gmt7
import json
import logging
import requests
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.schemas.profile import (
    GetMeResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UserProfileResponse
)


logger = logging.getLogger(__name__)

security = HTTPBearer()

# User table view ID for profile queries
USER_PROFILE_VIEW_ID = "viw6ye3dhnsRIJXAV4p"

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
            time_expired=parse_datetime_to_gmt7(fields.get("time_expired")),
            tax_code=fields.get("tax_code"),
            bank_name=fields.get("bank_name"),
            bank_number=fields.get("bank_number"),
            account_name=fields.get("account_name")
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
        
        # Build update payload - only include fields that have values (not None)
        update_fields = {}
        
        # Only add fields that are not None
        if update_data.business_name is not None:
            update_fields["business_name"] = update_data.business_name
        
        if update_data.tax_code is not None:
            update_fields["tax_code"] = update_data.tax_code
            
        if update_data.bank_name is not None:
            update_fields["bank_name"] = update_data.bank_name
            
        if update_data.bank_number is not None:
            update_fields["bank_number"] = update_data.bank_number
            
        if update_data.account_name is not None:
            update_fields["account_name"] = update_data.account_name
        
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