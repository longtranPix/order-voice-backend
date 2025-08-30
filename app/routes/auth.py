from fastapi import APIRouter
from app.schemas.auth import Account, SignUp, ChangePasswordRequest, ChangePasswordResponse
from app.services.auth_service import signin_service, signup_service, change_password_service

router = APIRouter()

@router.post("/signin")
async def signin(account: Account):
    """User signin endpoint"""
    return await signin_service(account)

@router.post("/signup")
async def signup(account: SignUp):
    """User signup endpoint"""
    return await signup_service(account)

@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(change_data: ChangePasswordRequest):
    """
    Change user password endpoint
    
    **Request Body:**
    ```json
    {
        "username": "user_taxcode",
        "old_password": "current_password",
        "new_password": "new_password"
    }
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "detail": "Đổi mật khẩu thành công",
        "username": "user_taxcode"
    }
    ```
    
    **Process:**
    1. Verify user credentials with username + old password
    2. If verification successful, update to new password with encoding
    3. Uses same password encoding rules as signup
    
    **Error Cases:**
    - Invalid username or old password: 401 Unauthorized
    - Server error during update: 500 Internal Server Error
    """
    return await change_password_service(change_data.dict())
