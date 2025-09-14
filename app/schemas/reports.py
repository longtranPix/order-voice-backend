"""
Report schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportRequest(BaseModel):
    """Schema for report request with date range"""
    start_date: datetime
    end_date: datetime

class ReportResponse(BaseModel):
    """Schema for report response"""
    status: str
    message: str
    data: dict
