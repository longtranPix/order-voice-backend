from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Account(BaseModel):
    username: str = Field(..., description="Tax code (e.g., '0316316874')")
    password: str = Field(..., description="User password")

class SignUp(BaseModel):
    username: str = Field(..., description="Tax code (e.g., '0316316874')")
    password: str = Field(..., description="User password")

class SignUpResponse(BaseModel):
    status: str
    detail: str
    account_id: str
    business_name: str
    taxcode: str
    workspace: Dict[str, Any]
    tables: Dict[str, str]
    upload_file_id: Optional[str] = None

class SignInResponse(BaseModel):
    status: str
    accessToken: str
    detail: str
    record: list

class TokenData(BaseModel):
    username: Optional[str] = None

"""
User profile schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    username: str
    business_name: str
    current_plan_name: Optional[str] = None
    last_login: Optional[datetime] = None
    time_expired: Optional[datetime] = None
    tax_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_number: Optional[str] = None
    account_name: Optional[str] = None

class GetMeResponse(BaseModel):
    """Schema for /me API response"""
    status: str
    message: str
    data: UserProfileResponse

class UpdateProfileRequest(BaseModel):
    """Schema for update profile request"""
    business_name: Optional[str] = None
    tax_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_number: Optional[str] = None
    account_name: Optional[str] = None
    password: Optional[str] = None
    # Add other editable fields as needed

class UpdateProfileResponse(BaseModel):
    """Schema for update profile response"""
    status: str
    message: str
    data: UserProfileResponse
