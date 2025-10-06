from fastapi import APIRouter, Depends, Query
from app.dependencies.auth import get_current_user
from app.services.report_service import sales_report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales")
async def sales_report(
    start_date: str = Query(..., description="Start date in ISO format (e.g., 2025-10-21T11:01:26.000Z)"),
    end_date: str = Query(..., description="End date in ISO format (e.g., 2025-10-21T11:01:26.000Z)"),
    current_user: str = Depends(get_current_user)
):
    """
    Sales report for a date range (inclusive). 
    Provide start_date and end_date in ISO format: "2025-10-21T11:01:26.000Z"
    """
    return await sales_report_service(current_user, start_date, end_date)



