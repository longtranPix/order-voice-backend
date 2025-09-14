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
    
    **Response:**
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
                "total_temp": 5000000,
                "total_vat": 500000,
                "total_with_tax": 5500000,
                "max_total_day": 500000,
                "max_total_date": "2025-01-15"
            },
            "daily_breakdown": {
                "2025-01-01": 200000,
                "2025-01-02": 300000,
                "2025-01-15": 500000
            }
        }
    }
    ```
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
