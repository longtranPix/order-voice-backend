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
    current_plan_name: str
    last_login: Optional[datetime] = None
    time_expired: Optional[datetime] = None

class GetMeResponse(BaseModel):
    """Schema for /me API response"""
    status: str
    message: str
    data: UserProfileResponse

class UpdateProfileRequest(BaseModel):
    """Schema for update profile request"""
    business_name: Optional[str] = None
    # Add other editable fields as needed

class UpdateProfileResponse(BaseModel):
    """Schema for update profile response"""
    status: str
    message: str
    data: UserProfileResponse
