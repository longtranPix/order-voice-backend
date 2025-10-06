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
        start_date_str: Start date in ISO format (e.g., "2025-10-21T11:01:26.000Z")
        end_date_str: End date in ISO format (e.g., "2025-10-21T11:01:26.000Z")
    
    Returns:
        List of date strings in YYYY-MM-DD format
    """
    try:
        logger.info(f"Generating date range from {start_date_str} to {end_date_str}")
        
        # Handle different ISO format variations
        def parse_iso_date(date_str: str) -> datetime:
            # Remove any trailing 'T' characters that might cause issues
            date_str = date_str.replace('T', 'T', 1) if 'T' in date_str else date_str
            
            # Handle Z suffix
            if date_str.endswith('Z'):
                date_str = date_str.replace('Z', '+00:00')
            
            # Parse the datetime
            return datetime.fromisoformat(date_str)
        
        # Parse ISO datetime strings
        start_date = parse_iso_date(start_date_str)
        end_date = parse_iso_date(end_date_str)
        
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


async def sales_report_service(current_user: str, start_date_str: str, end_date_str: str) -> Dict:
    """
    Build sales report for a date range [start_date, end_date].
    
    Args:
        current_user: Username of the current user
        start_date_str: Start date in ISO format (e.g., "2025-10-21T11:01:26.000Z")
        end_date_str: End date in ISO format (e.g., "2025-10-21T11:01:26.000Z")
    
    Returns:
    - total: sum of total_after_vat in range
    - total_cash: sum where payment_method == "Tiền mặt"
    - total_transfer: sum where payment_method == "Chuyển khoản"
    - by_days: [{date: YYYY-MM-DD, total: number}] for ALL days in range (including days with 0 sales)
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
            "pageSize": 1000,
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {
                        "fieldId": "createdTime",
                        "operator": "isOnOrAfter",
                        "value": start_date_str
                    },
                    {
                        "fieldId": "createdTime",
                        "operator": "isOnOrBefore",
                        "value": end_date_str
                    }
                ]
            })
        }

        result = handle_teable_api_call("GET", order_url, params=params, headers=headers)
        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể lấy danh sách đơn hàng: {result.get('error', 'Unknown error')}"
            )

        records: List[Dict] = result.get("data", {}).get("records", [])

        # 4) Generate complete date range
        all_dates = generate_date_range(start_date_str, end_date_str)
        if not all_dates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể tạo dải ngày từ dữ liệu đầu vào"
            )
        
        # 5) Initialize per_day with all dates (set to 0)
        per_day: Dict[str, float] = {date: 0.0 for date in all_dates}
        
        # 6) Aggregate totals from actual orders
        total = 0.0
        total_cash = 0.0
        total_transfer = 0.0

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

        # 7) Create by_days with all dates in chronological order
        by_days = [
            {"date": day, "total": per_day[day]}
            for day in sorted(per_day.keys())
        ]

        return {
            "status": "success",
            "total": total,
            "total_cash": total_cash,
            "total_transfer": total_transfer,
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



