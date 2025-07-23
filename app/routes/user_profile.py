"""
User profile routes for getting and updating user information
"""
from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
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
            "access_token": "teable_accWhxU2ZkU3O9brgx8_hprrcGxBozswLxEaJSW6J5MGhQ3BmuGf92NG3xGkON0=",
            "business_name": "Công ty Cổ phần CUBABLE",
            "current_plan_name": "Nâng cao",
            "last_login": "2025-07-08T03:28:23.478Z",
            "name": "27102001",
            "id": "recoR6uUjgMyHgmOMcP",
            "autoNumber": 38,
            "createdTime": "2025-07-06T18:12:35.439Z",
            "lastModifiedTime": "2025-07-08T10:28:19.052Z",
            "createdBy": "usr6cQql0CGD5qqSuPX",
            "lastModifiedBy": "usr6cQql0CGD5qqSuPX"
        }
    }
    ```
    """
    try:
        # Convert current_user data to proper response format
        # Import the utility function for datetime parsing
        from app.services.user_profile_service import parse_datetime_to_gmt7

        # Create UserProfileResponse from current_user data
        from app.schemas.user_profile import UserProfileResponse, GetMeResponse

        user_profile = UserProfileResponse(
            username=current_user.get("username", ""),
            business_name=current_user.get("business_name", ""),
            current_plan_name=current_user.get("current_plan_name"),
            last_login=parse_datetime_to_gmt7(current_user.get("last_login")),
            time_expired=parse_datetime_to_gmt7(current_user.get("time_expired"))
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
        "business_name": "Công ty Cổ phần CUBABLE Updated"
    }
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "message": "Cập nhật thông tin thành công",
        "data": {
            "username": "27102001",
            "access_token": "teable_accWhxU2ZkU3O9brgx8_hprrcGxBozswLxEaJSW6J5MGhQ3BmuGf92NG3xGkON0=",
            "business_name": "Công ty Cổ phần CUBABLE Updated",
            "current_plan_name": "Nâng cao",
            "last_login": "2025-07-08T03:28:23.478Z",
            "name": "27102001",
            "id": "recoR6uUjgMyHgmOMcP",
            "autoNumber": 38,
            "createdTime": "2025-07-06T18:12:35.439Z",
            "lastModifiedTime": "2025-07-08T10:28:19.052Z",
            "createdBy": "usr6cQql0CGD5qqSuPX",
            "lastModifiedBy": "usr6cQql0CGD5qqSuPX"
        }
    }
    ```
    
    **Notes:**
    - Only `business_name` field can be edited currently
    - Fields with `null` or `None` values will not be included in the update payload
    - If no fields are provided for update, returns current profile without changes
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
