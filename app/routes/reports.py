from fastapi import APIRouter, Depends, Query
from app.dependencies.auth import get_current_user
from app.services.report_service import sales_report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales")
async def sales_report(
    start_date: str = Query(..., description="Start date in ISO format (e.g., 2025-10-21T11:01:26.000Z) or simple date (e.g., 2025-10-21)"),
    end_date: str = Query(..., description="End date in ISO format (e.g., 2025-10-21T11:01:26.000Z) or simple date (e.g., 2025-10-21)"),
    current_user: str = Depends(get_current_user)
):
    """
    Sales report for a date range (inclusive).
    
    **Date Formats Supported:**
    - ISO format: "2025-10-21T11:01:26.000Z"
    - Simple date: "2025-10-21"
    
    **Breakdown Behavior:**
    - **Single Day (start_date = end_date):** Returns hourly breakdown object with all 24 hours
      - Example: `{"00h": 0, "01h": 0, "09h": 200000, "14h": 300000, ..., "23h": 0}`
    - **Multiple Days:** Returns daily breakdown object with all dates in range
      - Example: `{"2025-01-01": 200000, "2025-01-02": 0, "2025-01-03": 0, "2025-01-04": 0, "2025-01-05": 300000}`
    
    **Response Fields:**
    - `total`: Total sales amount
    - `total_cash`: Total cash payments
    - `total_transfer`: Total bank transfer payments
    - `count`: Number of orders
    - `breakdown`: Dictionary/Object with hour keys (single day) or date keys (multiple days)
    - `by_days`: (Multi-day only) Array format [{date, total}], kept for backward compatibility
    """
    return await sales_report_service(current_user, start_date, end_date)



