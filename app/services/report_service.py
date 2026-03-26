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
from datetime import datetime, timedelta

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
        
        # Get start of day and end of day in local time (GMT+7)
        local_start = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        local_end = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999000)
        
        # Convert local GMT+7 times to UTC for Teable API filters
        utc_start = local_start - timedelta(hours=7)
        utc_end = local_end - timedelta(hours=7)
        
        start_date_str = utc_start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_date_str = utc_end.strftime("%Y-%m-%dT%H:%M:%S.999Z")
        
        # Query orders within date range using created_time field with proper Teable filter format
        order_url = f"{settings.TEABLE_BASE_URL}/table/{order_table_id}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {
                        "fieldId": "created_time",
                        "operator": "isOnOrAfter",
                        "value": {
                            "mode": "exactDate",
                            "exactDate": start_date_str,
                            "timeZone": "Asia/Saigon"
                        }
                    },
                    {
                        "fieldId": "created_time",
                        "operator": "isOnOrBefore", 
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
        
        # Check if start and end date are on the same day
        is_same_day = start_date.date() == end_date.date()
        
        # Calculate aggregated statistics
        total = 0
        total_cash = 0
        total_transfer = 0
        daily_totals = {}  # Track daily totals
        hourly_totals = {}  # Track hourly totals for same-day queries
        
        for record in records:
            fields = record.get("fields", {})
            created_time = fields.get("created_time")
            payment_method = fields.get("payment_method")
            
            # Get totals from rollup fields
            with_tax = fields.get("total_with_tax", 0) or 0
            
            total += with_tax
            if payment_method == "Tiền mặt":
                total_cash += with_tax
            elif payment_method == "Chuyển khoản":
                total_transfer += with_tax
            
            if created_time:
                try:
                    # Convert created_time from UTC to local time (GMT+7)
                    dt_utc = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    dt_local = dt_utc + timedelta(hours=7)
                    
                    if is_same_day:
                        # Track hourly totals for same-day queries
                        hour = dt_local.hour
                        hour_key = f"{hour:02d}h"
                        if hour_key not in hourly_totals:
                            hourly_totals[hour_key] = 0
                        hourly_totals[hour_key] += with_tax
                    else:
                        # Track daily totals for multi-day queries
                        date_str = dt_local.strftime("%Y-%m-%d")
                        if date_str not in daily_totals:
                            daily_totals[date_str] = 0
                        daily_totals[date_str] += with_tax
                except Exception as e:
                    logger.warning(f"Failed to parse created_time: {created_time}, error: {e}")
        
        # For same-day queries, ensure all 24 hours are present
        if is_same_day:
            for hour in range(24):
                hour_key = f"{hour:02d}h"
                if hour_key not in hourly_totals:
                    hourly_totals[hour_key] = 0
            # Sort hourly totals by hour
            hourly_totals = dict(sorted(hourly_totals.items()))
        else:
            # For multi-day queries, ensure all days in range are present
            current_date = start_date.date()
            end_date_only = end_date.date()
            while current_date <= end_date_only:
                date_str = current_date.strftime("%Y-%m-%d")
                if date_str not in daily_totals:
                    daily_totals[date_str] = 0
                current_date += timedelta(days=1)
            # Sort daily totals by date
            daily_totals = dict(sorted(daily_totals.items()))
        
        # Find the day/hour with maximum total
        max_total_day = 0
        max_total_date = None
        if is_same_day and hourly_totals:
            max_total_date = max(hourly_totals.keys(), key=lambda x: hourly_totals[x])
            max_total_day = hourly_totals[max_total_date]
        elif daily_totals:
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
                "total": total,
                "total_cash": total_cash,
                "total_transfer": total_transfer,
                "max_total_day": max_total_day,
                "max_total_date": max_total_date
            }
        }
        
        # Add appropriate breakdown based on query type
        if is_same_day:
            report_data["breakdown"] = hourly_totals
        else:
            report_data["breakdown"] = daily_totals
        
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
