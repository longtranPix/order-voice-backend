import hmac
import hashlib
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import requests
from app.constants.auth_data import (
    PASSWORD_PREFIX, PASSWORD_SUFFIX, SECRET_KEY_PREFIX, SALT_PREFIX
)
import json

from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

def encode_password(password: str, username: str) -> str:
    """
    Encode password using private rules for secure storage
    
    Private encoding rules:
    1. Combine password with username as salt
    2. Apply HMAC-SHA256 with secret key
    3. Add timestamp-based rotation
    4. Base64 encode final result
    """
    try:
        # Private rule 1: Create salt from username with rotation
        salt = f"{username}{SALT_PREFIX}{len(password)}"

        # Private rule 2: Create secret key from multiple sources
        secret_key = f"{SECRET_KEY_PREFIX}{username[:3]}_{len(username)}_ORDER_VOICE_2025"

        # Private rule 3: Combine password with salt and apply transformations
        combined = f"{password}:{salt}:{len(password + username)}"

        # Private rule 4: Apply HMAC-SHA256 with secret key
        encoded_bytes = hmac.new(
            secret_key.encode('utf-8'),
            combined.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Private rule 5: Add additional layer with base64 and custom suffix
        final_encoded = base64.b64encode(encoded_bytes).decode('utf-8')

        # Private rule 6: Add custom prefix and suffix for identification
        result = f"{PASSWORD_PREFIX}{final_encoded}{PASSWORD_SUFFIX}"

        return result

    except Exception as e:
        logger.error(f"Password encoding error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi mã hóa mật khẩu"
        )

async def get_user_table_info(user: Union[str, dict]) -> dict:
    """Get user table information using viewId. Accepts username str or user payload dict."""
    try:
        # Extract username from either a dict (from token) or a raw string
        if isinstance(user, dict):
            username = user.get("username")
        else:
            username = str(user)

        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Get user table info with specific viewId
        logger.info(f"Getting user table info for {username}")
        logger.info(f"User view ID: {settings.TEABLE_USER_VIEW_ID}")
        logger.info(f"User table URL: {settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record")
        logger.info(f"User table ID: {settings.TEABLE_TABLE_ID}")
        user_table_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "viewId": settings.TEABLE_USER_VIEW_ID,
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": username}
                ]
            })
        }

        result = handle_teable_api_call("GET", user_table_url, params=params, headers=headers)

        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể lấy thông tin người dùng: {result.get('error', 'Unknown error')}"
            )

        records = result.get("data", {}).get("records", [])
        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông tin người dùng"
            )

        user_fields = records[0].get("fields", {})
        logger.info(f"Retrieved user table info for {username}")
        logger.info(f"User fields: {user_fields}")
        return user_fields

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user table info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin người dùng: {str(e)}"
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

def verify_password(password: str, username: str, encoded_password: str) -> bool:
    """Verify password against encoded password"""
    try:
        expected_encoded = encode_password(password, username)
        return expected_encoded == encoded_password
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def create_invoice_token(username: str, password: str) -> str:
    """Create invoice token for API access"""
    try:
        raw_string = f"{username}:{password}"
        encoded_bytes = base64.b64encode(raw_string.encode("utf-8"))
        return encoded_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Invoice token creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi tạo token hóa đơn"
        )

def handle_teable_api_call(method: str, url: str, **kwargs) -> dict:
    """Handle Teable API calls with error handling"""
    import requests
    
    try:
        response = requests.request(method, url, **kwargs)
        
        if response.status_code in [200, 201]:
            return {
                "success": True,
                "data": response.json(),
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 500
        }

def update_user_table_id(table_id: str, record_id: str, update_fields: dict, teable_token: str, teable_base_url: str) -> bool:
    """Update user table record with new fields"""
    try:
        headers = {
            "Authorization": teable_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        update_payload = {
            "typecast": True,
            "records": [{
                "id": record_id,
                "fields": update_fields
            }],
            "fieldKeyType": "dbFieldName"
        }
        
        update_url = f"{teable_base_url}/table/{table_id}/record"
        result = handle_teable_api_call("PATCH", update_url, data=json.dumps(update_payload), headers=headers)
        
        return result["success"]
    except Exception as e:
        logger.error(f"Error updating user table: {str(e)}")
        return False
