"""
Report service for generating order statistics
"""
import json
import logging
import requests
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.reports import ReportRequest, ReportResponse
from app.utils.auth_utils import get_user_table_info
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_order_report_service(current_user: dict, start_date: datetime, end_date: datetime) -> ReportResponse:
    """
    Get order report with aggregated statistics for date range
    """
    try:
        # Get user's table IDs
        username = current_user.get("username")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username not found in current user data"
            )
        
        user_fields = await get_user_table_info(current_user)
        order_table_id = user_fields.get("table_order_id")
        
        if not order_table_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order table ID not found for user"
            )
        
        # Prepare headers
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Format dates for Teable API - start date to beginning of day, end date to end of day
        start_date_str = start_date.strftime("%Y-%m-%dT00:00:00.000Z")
        end_date_str = end_date.strftime("%Y-%m-%dT23:59:59.999Z")
        
        # Query orders within date range using created_time field with proper Teable filter format
        order_url = f"{settings.TEABLE_BASE_URL}/table/{order_table_id}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {
                        "fieldId": "created_time",
                        "operator": "isAfter",
                        "value": {
                            "mode": "exactDate",
                            "exactDate": start_date_str,
                            "timeZone": "Asia/Saigon"
                        }
                    },
                    {
                        "fieldId": "created_time",
                        "operator": "isBefore", 
                        "value": {
                            "mode": "exactDate",
                            "exactDate": end_date_str,
                            "timeZone": "Asia/Saigon"
                        }
                    }
                ]
            })
        }
        
        logger.info(f"Getting orders for user {username} from {start_date_str} to {end_date_str}")
        
        # Make the API call
        response = requests.get(order_url, headers=headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"Teable API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi khi lấy dữ liệu đơn hàng: {response.status_code}"
            )
        
        data = response.json()
        records = data.get("records", [])
        
        logger.info(f"Found {len(records)} orders in date range")
        
        # Calculate aggregated statistics
        total_temp = 0
        total_vat = 0
        total_with_tax = 0
        daily_totals = {}  # Track daily totals
        
        for record in records:
            fields = record.get("fields", {})
            created_time = fields.get("created_time")
            
            # Get totals from rollup fields
            temp = fields.get("total_temp", 0) or 0
            vat = fields.get("total_vat_price", 0) or 0
            with_tax = fields.get("total_with_tax", 0) or 0
            
            total_temp += temp
            total_vat += vat
            total_with_tax += with_tax
            
            # Track daily totals
            if created_time:
                # Extract date part (YYYY-MM-DD)
                date_str = created_time.split('T')[0]
                if date_str not in daily_totals:
                    daily_totals[date_str] = 0
                daily_totals[date_str] += with_tax
        
        # Find the day with maximum total
        max_total_day = 0
        max_total_date = None
        if daily_totals:
            max_total_date = max(daily_totals.keys(), key=lambda x: daily_totals[x])
            max_total_day = daily_totals[max_total_date]
        
        # Prepare response data
        report_data = {
            "date_range": {
                "start_date": start_date_str,
                "end_date": end_date_str
            },
            "summary": {
                "total_orders": len(records),
                "total_temp": total_temp,
                "total_vat": total_vat,
                "total_with_tax": total_with_tax,
                "max_total_day": max_total_day,
                "max_total_date": max_total_date
            },
            "daily_breakdown": daily_totals
        }
        
        logger.info(f"Report generated successfully for {len(records)} orders")
        
        return ReportResponse(
            status="success",
            message="Báo cáo đơn hàng được tạo thành công",
            data=report_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_order_report_service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )
