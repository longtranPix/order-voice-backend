import json
import requests
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.orders import CreateOrderRequest

async def create_order_service(data: CreateOrderRequest) -> dict:
    """Handle order creation"""
    try:
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Calculate totals
        total_temp = sum(item.unit_price * item.quantity for item in data.order_details)
        total_vat = sum(item.unit_price * item.quantity * item.vat / 100 for item in data.order_details)
        total_after_vat = total_temp + total_vat

        # Create order details
        detail_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{"fields": d.model_dump()} for d in data.order_details]
        }
        detail_url = f"{settings.TEABLE_BASE_URL}/table/{data.detail_table_id}/record"
        response_detail = requests.post(detail_url, data=json.dumps(detail_payload), headers=headers)
        if response_detail.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không thể tạo chi tiết đơn hàng: {response_detail.text}")

        detail_records = response_detail.json().get("records", [])
        detail_ids = [r["id"] for r in detail_records]

        # Create main order
        order_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": {
                    "customer_name": data.customer_name,
                    "invoice_details": detail_ids,
                    "total_temp": total_temp,
                    "total_vat": total_vat,
                    "total_after_vat": total_after_vat
                }
            }]
        }
        order_url = f"{settings.TEABLE_BASE_URL}/table/{data.order_table_id}/record"
        response_order = requests.post(order_url, data=json.dumps(order_payload), headers=headers)
        if response_order.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không thể tạo đơn hàng: {response_order.text}")

        return {
            "status": "success",
            "order": response_order.json(),
            "total_temp": total_temp,
            "total_vat": total_vat,
            "total_after_vat": total_after_vat
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi không mong muốn khi tạo đơn hàng: {str(e)}")
