"""
User profile routes for getting and updating user information
"""
from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
import logging
from app.schemas.user_profile import (
    GetMeResponse, 
    UpdateProfileRequest, 
    UpdateProfileResponse
)
from app.services.user_profile_service import (
    update_user_profile_by_authorization
)
from app.services.user_profile_service import get_current_user_profile

router = APIRouter(prefix="/user", tags=["user_profile"])
logger = logging.getLogger(__name__)

@router.get("/me", response_model=GetMeResponse)
async def get_me(current_user: dict = Depends(get_current_user_profile)):
    """
    Get current user profile information
    
    **Headers:**
    - Authorization: Bearer {access_token}
    
    **Response:**
    ```json
    {
        "status": "success",
        "message": "Lấy thông tin người dùng thành công",
        "data": {
            "username": "27102001",
            "business_name": "Công ty Cổ phần CUBABLE",
            "current_plan_name": "Nâng cao",
            "last_login": "2025-07-08T03:28:23.478Z",
            "time_expired": "2025-07-08T03:28:23.478Z",
            "tax_code": "0123456789",
            "bank_name": "Vietcombank",
            "bank_number": "1234567890",
            "account_name": "Công ty Cổ phần CUBABLE"
        }
    }
    ```
    """
    try:
        # Convert current_user data to proper response format
        # Import the utility function for datetime parsing
        logger.info('check: ', current_user)
        from app.services.user_profile_service import parse_datetime_to_gmt7

        # Create UserProfileResponse from current_user data
        from app.schemas.user_profile import UserProfileResponse, GetMeResponse

        user_profile = UserProfileResponse(
            username=current_user.get("username", ""),
            business_name=current_user.get("business_name", ""),
            current_plan_name=current_user.get("current_plan_name"),
            last_login=parse_datetime_to_gmt7(current_user.get("last_login")),
            time_expired=parse_datetime_to_gmt7(current_user.get("time_expired")),
            tax_code=current_user.get("tax_code"),
            bank_name=current_user.get("bank_name"),
            bank_number=current_user.get("bank_number"),
            account_name=current_user.get("account_name")
        )

        return GetMeResponse(
            status="success",
            message="Lấy thông tin người dùng thành công",
            data=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )

@router.patch("/update-profile", response_model=UpdateProfileResponse)
async def update_profile(
    update_data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user_profile)
):
    """
    Update user profile information
    
    **Headers:**
    - Authorization: Bearer {access_token}
    
    **Request Body:**
    ```json
    {
        "business_name": "Công ty Cổ phần CUBABLE Updated",
        "tax_code": "0123456789",
        "bank_name": "Vietcombank",
        "bank_number": "1234567890",
        "account_name": "Công ty Cổ phần CUBABLE"
    }
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "message": "Cập nhật thông tin thành công",
        "data": {
            "username": "27102001",
            "business_name": "Công ty Cổ phần CUBABLE Updated",
            "current_plan_name": "Nâng cao",
            "last_login": "2025-07-08T03:28:23.478Z",
            "time_expired": "2025-07-08T03:28:23.478Z",
            "tax_code": "0123456789",
            "bank_name": "Vietcombank",
            "bank_number": "1234567890",
            "account_name": "Công ty Cổ phần CUBABLE"
        }
    }
    ```
    
    **Notes:**
    - Tất cả các trường đều là optional
    - Chỉ những trường có giá trị (không null) mới được cập nhật
    - Trường với giá trị `null` hoặc `None` sẽ không được đưa vào payload cập nhật
    - Nếu không có trường nào được cung cấp để cập nhật, API sẽ trả về profile hiện tại mà không thay đổi
    """
    try:
        # Update user profile using Authorization header
        return await update_user_profile_by_authorization(update_data, current_user.get("id"))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )
