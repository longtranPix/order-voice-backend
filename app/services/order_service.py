import json
import requests
import logging
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.orders import CreateOrderRequest
from app.services.plan_status_service import reduce_credit_value_on_order_complete
from app.utils.auth_utils import get_user_table_info

logger = logging.getLogger(__name__)

async def create_order_service(data: CreateOrderRequest, current_user: dict) -> dict:
    """Handle order creation"""
    try:
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Get user's table IDs using helper
        # username = current_user.get("sub")
        user_fields = await get_user_table_info(current_user)
        order_table_id = user_fields.get("table_order_id")
        detail_table_id = user_fields.get("table_order_detail_id")
        logger.info(f"Order table id: {order_table_id}")
        logger.info(f"Detail table id: {detail_table_id}")

        # Optional: local totals (computed by Teable as rollups, not sent)
        total_temp = sum(item.unit_price * item.quantity for item in data.order_details)
        total_vat = sum(item.unit_price * item.quantity * item.vat_rate / 100 for item in data.order_details)
        total_after_vat = total_temp + total_vat

        # Create order details
        detail_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [
                {
                    "fields": {
                        "product_name": d.product_name,
                        "unit_price": d.unit_price,
                        "quantity": d.quantity,
                        "vat_rate": d.vat_rate
                    }
                }
                for d in data.order_details
            ]
        }
        detail_url = f"{settings.TEABLE_BASE_URL}/table/{detail_table_id}/record"
        response_detail = requests.post(detail_url, data=json.dumps(detail_payload), headers=headers)
        if response_detail.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không thể tạo chi tiết đơn hàng: {response_detail.text}")

        detail_records = response_detail.json().get("records", [])
        detail_ids = [r["id"] for r in detail_records]

        # Create main order. Only provide fields present in order schema
        order_fields = {
            "detail_orders": detail_ids
        }
        
        # Add order_code if provided
        if data.order_code:
            order_fields["order_code"] = data.order_code
        
        # Add customer_name if provided
        if data.customer_name:
            order_fields["customer_name"] = data.customer_name
        
        # Add payment_method if provided
        if data.payment_method:
            order_fields["payment_method"] = data.payment_method
            
        order_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": order_fields
            }]
        }
        order_url = f"{settings.TEABLE_BASE_URL}/table/{order_table_id}/record"
        response_order = requests.post(order_url, data=json.dumps(order_payload), headers=headers)
        if response_order.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không thể tạo đơn hàng: {response_order.text}")
        # Step 6: Reduce credit value after successful order completion
        credit_reduced = await reduce_credit_value_on_order_complete(current_user)
        if credit_reduced:
            logger.info(f"Successfully reduced credit value for user {current_user} after order completion")
        else:
            logger.warning(f"Failed to reduce credit value for user {current_user}, but order was created successfully")

        logger.info(f"Successfully created order {order_table_id} for user {current_user}")
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
