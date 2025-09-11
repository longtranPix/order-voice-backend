import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import Account, SignUp, SignUpResponse, SignInResponse
from app.services.auth_service import signin_service, signup_service
from app.utils.jwt_auth import get_current_user, get_current_active_user, create_teable_token_payload
from app.utils.auth_utils import get_current_user_profile, verify_password, get_user_table_info

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/signin", response_model=SignInResponse)
async def signin(account: Account):
    """User signin endpoint"""
    return await signin_service(account)

@router.post("/signup", response_model=SignUpResponse)
async def signup(account: SignUp):
    """User signup endpoint"""
    return await signup_service(account)

@router.get("/me")
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
        from app.utils.auth_utils import parse_datetime_to_gmt7

        # Create UserProfileResponse from current_user data
        from app.schemas.auth import UserProfileResponse, GetMeResponse

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

@router.post("/refresh")
async def refresh_token(current_user: dict = Depends(get_current_active_user)):
    """Refresh access token"""
    # This would typically involve checking if the user is still valid
    # and generating a new token with extended expiry
    return {
        "status": "success",
        "detail": "Token refreshed successfully",
        "user": current_user.get("sub")
    }
