import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import HTTPException, status

from app.core.config import settings
from app.services.auth_service import get_user_table_info
from app.services.teable_service import handle_teable_api_call
# Removed import of get_table_id_fast - now using old method of table ID storage

logger = logging.getLogger(__name__)


def generate_date_range(start_date_str: str, end_date_str: str) -> List[str]:
    """
    Generate list of all dates between start_date and end_date (inclusive).
    
    Args:
        start_date_str: Start date in ISO format (e.g., "2025-10-21T11:01:26.000Z") or simple date (e.g., "2025-10-21")
        end_date_str: End date in ISO format (e.g., "2025-10-21T11:01:26.000Z") or simple date (e.g., "2025-10-21")
    
    Returns:
        List of date strings in YYYY-MM-DD format
    """
    try:
        logger.info(f"Generating date range from {start_date_str} to {end_date_str}")
        
        # Handle different date format variations
        def parse_date(date_str: str) -> datetime:
            # Handle simple date format (YYYY-MM-DD)
            if len(date_str) == 10 and date_str.count('-') == 2:
                return datetime.fromisoformat(date_str + "T00:00:00+00:00")
            
            # Handle full ISO datetime format
            if date_str.endswith('Z'):
                date_str = date_str.replace('Z', '+00:00')
            
            # Parse the datetime
            return datetime.fromisoformat(date_str)
        
        # Parse date strings
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        
        # Convert to date objects (remove time component)
        start_date = start_date.date()
        end_date = end_date.date()
        
        logger.info(f"Parsed dates: {start_date} to {end_date}")
        
        # Generate all dates in range
        date_list = []
        current_date = start_date
        
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {len(date_list)} dates in range")
        return date_list
        
    except Exception as e:
        logger.error(f"Error generating date range: {str(e)}")
        logger.error(f"Start date string: {start_date_str}")
        logger.error(f"End date string: {end_date_str}")
        return []


def generate_hours_range() -> List[str]:
    """
    Generate list of all 24 hours in format "00h", "01h", ..., "23h"
    
    Returns:
        List of hour strings in HHh format
    """
    return [f"{hour:02d}h" for hour in range(24)]


def is_same_day(start_date_str: str, end_date_str: str) -> bool:
    """
    Check if start_date and end_date are on the same day.
    
    Args:
        start_date_str: Start date in ISO format or simple date
        end_date_str: End date in ISO format or simple date
    
    Returns:
        True if both dates are on the same day, False otherwise
    """
    try:
        def parse_date(date_str: str) -> datetime:
            # Handle simple date format (YYYY-MM-DD)
            if len(date_str) == 10 and date_str.count('-') == 2:
                return datetime.fromisoformat(date_str + "T00:00:00+00:00")
            
            # Handle full ISO datetime format
            if date_str.endswith('Z'):
                date_str = date_str.replace('Z', '+00:00')
            
            # Parse the datetime
            return datetime.fromisoformat(date_str)
        
        start_date = parse_date(start_date_str).date()
        end_date = parse_date(end_date_str).date()
        
        return start_date == end_date
    except Exception:
        return False


async def sales_report_service(current_user: str, start_date_str: str, end_date_str: str) -> Dict:
    """
    Build sales report for a date range [start_date, end_date].
    
    Args:
        current_user: Username of the current user
        start_date_str: Start date in ISO format (e.g., "2025-10-21T11:01:26.000Z") or simple date (e.g., "2025-10-21")
        end_date_str: End date in ISO format (e.g., "2025-10-21T11:01:26.000Z") or simple date (e.g., "2025-10-21")
    
    Returns:
    - total: sum of total_after_vat in range
    - total_cash: sum where payment_method == "Tiền mặt"
    - total_transfer: sum where payment_method == "Chuyển khoản"
    - breakdown: Dictionary/object format
        - If single day: {"00h": 0, "01h": 0, ..., "23h": 0} for ALL 24 hours
        - If multiple days: {"2025-01-01": 200000, "2025-01-02": 0, ...} for ALL days in range
    - by_days: (kept for backward compatibility) array format [{date: YYYY-MM-DD, total: number}] for multiple days only
    """
    try:
        # 1) Load user workspace info
        user_info = await get_user_table_info(current_user)
        base_id = user_info.get("base_id")
        access_token = user_info.get("access_token")

        if not all([base_id, access_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu thông tin workspace của người dùng"
            )

        # 2) Get order table id from user table fields (old method)
        order_table_id = user_info.get("table_order_id")
        if not order_table_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không tìm thấy bảng đơn hàng trong thông tin người dùng"
            )

        # 3) Query orders in range
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        order_url = f"{settings.TEABLE_BASE_URL}/table/{order_table_id}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "pageSize": 1000
        }

        result = handle_teable_api_call("GET", order_url, params=params, headers=headers)
        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể lấy danh sách đơn hàng: {result.get('error', 'Unknown error')}"
            )

        all_records: List[Dict] = result.get("data", {}).get("records", [])
        
        # Filter orders by date range on client-side (since Teable API filtering by createdTime is broken)
        def parse_iso_date(date_str: str, is_start: bool = True) -> datetime:
            """Parse ISO datetime string or simple date string"""
            try:
                # Handle simple date format (YYYY-MM-DD)
                if len(date_str) == 10 and date_str.count('-') == 2:
                    # Convert simple date to datetime at start/end of day
                    if is_start:  # Start date - beginning of day
                        return datetime.fromisoformat(date_str + "T00:00:00+00:00")
                    else:  # End date - end of day
                        return datetime.fromisoformat(date_str + "T23:59:59+00:00")
                
                # Handle full ISO datetime format
                if date_str.endswith('Z'):
                    date_str = date_str.replace('Z', '+00:00')
                return datetime.fromisoformat(date_str)
            except Exception:
                return None
        
        start_date_obj = parse_iso_date(start_date_str, is_start=True)
        end_date_obj = parse_iso_date(end_date_str, is_start=False)
        
        if not start_date_obj or not end_date_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể parse ngày bắt đầu hoặc kết thúc"
            )
        
        # Filter records by date range
        records = []
        for record in all_records:
            created_time_str = record.get("createdTime")
            if created_time_str:
                created_time_obj = parse_iso_date(created_time_str)
                if created_time_obj and start_date_obj <= created_time_obj <= end_date_obj:
                    records.append(record)
        
        logger.info(f"Filtered {len(records)} orders from {len(all_records)} total orders for date range {start_date_str} to {end_date_str}")

        # 5) Check if it's a single day or multiple days
        single_day = is_same_day(start_date_str, end_date_str)
        
        # 6) Aggregate totals from actual orders
        total = 0.0
        total_cash = 0.0
        total_transfer = 0.0
        
        if single_day:
            # Single day: break down by hours (00h - 23h)
            logger.info("Single day detected - generating hourly breakdown")
            all_hours = generate_hours_range()
            per_hour: Dict[str, float] = {hour: 0.0 for hour in all_hours}
            
            for rec in records:
                fields = rec.get("fields", {})
                total_after_vat = fields.get("total_after_vat") or fields.get("final_total") or 0
                payment_method = fields.get("payment_method", "")
                
                # Get createdTime from record level (system field)
                created_time = rec.get("createdTime")

                # Sum global totals
                try:
                    amount = float(total_after_vat)
                except Exception:
                    amount = 0.0

                total += amount
                if payment_method == "Tiền mặt":
                    total_cash += amount
                if payment_method == "Chuyển khoản":
                    total_transfer += amount

                # Group by hour (HHh format)
                hour_key = None
                if isinstance(created_time, str):
                    try:
                        # Parse the datetime to extract hour
                        if created_time.endswith('Z'):
                            created_time_parsed = created_time.replace('Z', '+00:00')
                        else:
                            created_time_parsed = created_time
                        dt = datetime.fromisoformat(created_time_parsed)
                        hour_key = f"{dt.hour:02d}h"
                    except Exception as e:
                        logger.warning(f"Failed to parse hour from {created_time}: {str(e)}")
                        hour_key = None

                if hour_key and hour_key in per_hour:
                    per_hour[hour_key] += amount
                    logger.info(f"Added {amount:,.0f} VND to hour {hour_key}")
                elif hour_key:
                    logger.warning(f"Hour {hour_key} is not in expected range")

            # Create breakdown as dictionary with hour keys
            breakdown = {hour: per_hour[hour] for hour in all_hours}
            
            return {
                "status": "success",
                "total": total,
                "total_cash": total_cash,
                "total_transfer": total_transfer,
                "breakdown": breakdown,
                "count": len(records)
            }
        
        else:
            # Multiple days: break down by days
            logger.info("Multiple days detected - generating daily breakdown")
            all_dates = generate_date_range(start_date_str, end_date_str)
            if not all_dates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Không thể tạo dải ngày từ dữ liệu đầu vào"
                )
            
            # Initialize per_day with all dates (set to 0)
            per_day: Dict[str, float] = {date: 0.0 for date in all_dates}
            
            for rec in records:
                fields = rec.get("fields", {})
                total_after_vat = fields.get("total_after_vat") or fields.get("final_total") or 0
                payment_method = fields.get("payment_method", "")
                
                # Get createdTime from record level (system field)
                created_time = rec.get("createdTime")

                # Sum global totals
                try:
                    amount = float(total_after_vat)
                except Exception:
                    amount = 0.0

                total += amount
                if payment_method == "Tiền mặt":
                    total_cash += amount
                if payment_method == "Chuyển khoản":
                    total_transfer += amount

                # Group by day (YYYY-MM-DD)
                day_key = None
                if isinstance(created_time, str) and len(created_time) >= 10:
                    day_key = created_time[:10]
                else:
                    # Fallback: no date string; skip grouping
                    day_key = None

                if day_key and day_key in per_day:
                    per_day[day_key] += amount
                    logger.info(f"Added {amount:,.0f} VND to {day_key}")
                elif day_key:
                    # If day_key is outside our range, still count it in totals but not in per_day
                    logger.warning(f"Order date {day_key} is outside requested range {start_date_str} to {end_date_str}")

            # Create breakdown as dictionary with date keys (sorted by date)
            breakdown = {day: per_day[day] for day in sorted(per_day.keys())}
            
            # Keep by_days for backward compatibility (array format)
            by_days = [
                {"date": day, "total": per_day[day]}
                for day in sorted(per_day.keys())
            ]

            return {
                "status": "success",
                "total": total,
                "total_cash": total_cash,
                "total_transfer": total_transfer,
                "breakdown": breakdown,
                "by_days": by_days,
                "count": len(records)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building sales report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo báo cáo: {str(e)}"
        )



