"""
Plan status routes for retrieving plan information
"""
from fastapi import APIRouter
from app.schemas.plan_status import PlanStatusRequest, GetPlanStatusResponse
from app.services.plan_status_service import get_plan_status_service

router = APIRouter(prefix="/plan-status", tags=["plan_status"])

@router.post("/get-status-plan", response_model=GetPlanStatusResponse)
async def get_status_plan(request: PlanStatusRequest):
    """
    Get plan status information by plan_status_id
    
    **Request Body:**
    ```json
    {
        "plan_status_id": "recdDix5FO3DxcvYIoD"
    }
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "message": "Lấy thông tin plan status thành công",
        "data": {
            "fields": {
                "Nhan": 1,
                "So": {
                    "id": "rec5e5txg7k5USs1CZw",
                    "title": "4"
                },
                "started_time": "2025-07-15T08:44:38.952Z",
                "cycle": 12,
                "time_expired": "2026-07-15T08:44:38.952Z",
                "Ngay": "2025-07-15T09:04:00.000Z",
                "status": "Đang hoạt động",
                "credit_value": 4000,
                "Tai_khoan": {
                    "id": "recSzqmkuTChxV3rOiu",
                    "title": "25031989"
                },
                "name_plan": "Cơ bản"
            },
            "name": "1",
            "id": "recdDix5FO3DxcvYIoD",
            "autoNumber": 1,
            "createdTime": "2025-07-15T08:44:38.952Z",
            "lastModifiedTime": "2025-07-17T09:05:06.690Z",
            "createdBy": "usr6cQql0CGD5qqSuPX",
            "lastModifiedBy": "usr6cQql0CGD5qqSuPX"
        }
    }
    ```
    """
    return await get_plan_status_service(request)
