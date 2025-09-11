"""
Plan status schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

# No longer needed - plan status is retrieved from user's current_plan
# class PlanStatusRequest(BaseModel):
#     """Schema for plan status request"""
#     plan_status_id: str

class AccountInfo(BaseModel):
    """Schema for account information in plan status"""
    id: str
    title: str

class SoInfo(BaseModel):
    """Schema for So information in plan status"""
    id: str
    title: str

class PlanStatusFields(BaseModel):
    """Schema for plan status fields"""
    started_time: Optional[datetime] = None
    cycle: Optional[int] = None
    time_expired: Optional[datetime] = None
    status: Optional[str] = None
    credit_value: Optional[int] = None
    name_plan: Optional[str] = None

class PlanStatusResponse(BaseModel):
    """Schema for plan status response"""
    fields: PlanStatusFields
    name: str
    id: str
    autoNumber: int
    createdTime: datetime
    lastModifiedTime: datetime
    createdBy: str
    lastModifiedBy: str

class GetPlanStatusResponse(BaseModel):
    """Schema for get plan status API response"""
    status: str
    message: str
    data: PlanStatusResponse
