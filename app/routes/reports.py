"""
Report routes for generating order statistics
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.reports import ReportRequest, ReportResponse
from app.services.report_service import get_order_report_service
from app.utils.auth_utils import get_current_user_profile

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/order-report", response_model=ReportResponse)
async def get_order_report(
    request: ReportRequest,
    current_user: dict = Depends(get_current_user_profile)
):
    """
    Get order report with aggregated statistics for date range
    
    **Headers:**
    - Authorization: Bearer {access_token}
    
    **Request Body:**
    ```json
    {
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-31T23:59:59Z"
    }
    ```
    
    **Response (Multi-day):**
    ```json
    {
        "status": "success",
        "message": "Báo cáo đơn hàng được tạo thành công",
        "data": {
            "date_range": {
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-01-31T23:59:59Z"
            },
            "summary": {
                "total_orders": 25,
                "total": 5500000,
                "total_cash": 3000000,
                "total_transfer": 2500000,
                "max_total_day": 500000,
                "max_total_date": "2025-01-15"
            },
            "breakdown": {
                "2025-01-01": 200000,
                "2025-01-02": 300000,
                "2025-01-03": 0,
                "...": 0,
                "2025-01-15": 500000,
                "...": 0,
                "2025-01-31": 100000
            }
        }
    }
    ```
    
    **Response (Single-day with hourly breakdown):**
    ```json
    {
        "status": "success",
        "message": "Báo cáo đơn hàng được tạo thành công",
        "data": {
            "date_range": {
                "start_date": "2025-01-15T00:00:00Z",
                "end_date": "2025-01-15T23:59:59Z"
            },
            "summary": {
                "total_orders": 10,
                "total": 1500000,
                "total_cash": 800000,
                "total_transfer": 700000,
                "max_total_day": 300000,
                "max_total_date": "14h"
            },
            "breakdown": {
                "00h": 0,
                "01h": 0,
                "...": 0,
                "09h": 200000,
                "10h": 150000,
                "14h": 300000,
                "...": 0,
                "23h": 0
            }
        }
    }
    ```
    
    **Notes:**
    - The `breakdown` field contains either hourly or daily data depending on the query
    - Single-day queries: hourly breakdown with keys like "00h", "01h", ..., "23h" (all 24 hours included)
    - Multi-day queries: daily breakdown with keys like "2025-01-01", "2025-01-02", etc. (all days in range included)
    - All periods are included even if they have 0 orders/total
    """
    try:
        return await get_order_report_service(
            current_user, 
            request.start_date, 
            request.end_date
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi tạo báo cáo: {str(e)}"
        )
