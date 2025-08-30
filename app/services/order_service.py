import json
import logging
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.orders import CreateOrderRequest, CreateOrderResponse
from app.schemas.delivery_notes import CreateDeliveryNoteRequest, DeliveryNoteDetailItem
from app.services.import_slip_service import create_delivery_note_service
from app.services.auth_service import get_user_table_info
from app.services.teable_service import handle_teable_api_call
from app.services.plan_status_service import reduce_credit_value_on_order_complete

logger = logging.getLogger(__name__)

async def create_order_service(data: CreateOrderRequest, current_user: str) -> CreateOrderResponse:
    """Handle order creation with automatic delivery note creation"""
    try:
        # Step 1: Get user table information
        user_info = await get_user_table_info(current_user)

        # Extract required table IDs
        order_table_id = user_info.get("table_order_id")
        order_detail_table_id = user_info.get("table_order_detail_id")
        access_token = user_info.get("access_token")

        if not all([order_table_id, order_detail_table_id, access_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể lấy thông tin bảng người dùng"
            )

        # Set up headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Step 2: Calculate totals
        total_temp = sum(item.unit_price * item.quantity for item in data.order_details)
        total_vat = sum(item.unit_price * item.quantity * item.vat / 100 for item in data.order_details)
        total_after_vat = total_temp + total_vat

        # Step 3: Create order details with product_id and unit_conversions_id
        detail_records = []
        for detail in data.order_details:
            temp_total = detail.unit_price * detail.quantity
            final_total = temp_total + (temp_total * detail.vat / 100)

            detail_record = {
                "fields": {
                    "product_link": [detail.product_id],  # Link to product table
                    "unit_conversions": [detail.unit_conversions_id],  # Link to unit conversions
                    "unit_price": detail.unit_price,
                    "quantity": detail.quantity,
                    "vat": detail.vat,
                    "temp_total": temp_total,
                    "final_total": final_total
                }
            }
            detail_records.append(detail_record)

        # Create order details
        detail_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": detail_records
        }

        detail_url = f"{settings.TEABLE_BASE_URL}/table/{order_detail_table_id}/record"
        detail_result = handle_teable_api_call("POST", detail_url, data=json.dumps(detail_payload), headers=headers)

        if not detail_result["success"]:
            raise HTTPException(
                status_code=detail_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo chi tiết đơn hàng: {detail_result.get('error', 'Unknown error')}, order_detail_table_id: {order_detail_table_id}, detail_url: {detail_url}"
            )

        # Get created detail record IDs
        detail_records_created = detail_result.get("data", {}).get("records", [])
        detail_ids = [record["id"] for record in detail_records_created]

        # Step 4: Create main order
        # Prepare order fields
        order_fields = {
            "customer_link": [data.customer_id],  # Link to customer table
            "order_details": detail_ids,  # Link to created details
            "payment_method": data.payment_method  # Add payment method
        }
        
        # Check if payment method is "Chuyển khoản" and add status field
        if data.payment_method == "Chuyển khoản":
            order_fields["status"] = "Chưa Thanh Toán"
        
        order_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": order_fields
            }]
        }

        order_url = f"{settings.TEABLE_BASE_URL}/table/{order_table_id}/record"
        order_result = handle_teable_api_call("POST", order_url, data=json.dumps(order_payload), headers=headers)

        if not order_result["success"]:
            raise HTTPException(
                status_code=order_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo đơn hàng: {order_result.get('error', 'Unknown error')}"
            )

        # Get created order info
        order_record = order_result.get("data", {}).get("records", [{}])[0]
        order_id = order_record.get("id", "")
        order_code = order_record.get("fields", {}).get("order_code", "")

        # Step 5: Automatically create delivery note for this order
        delivery_note_details = []
        for detail in data.order_details:
            delivery_detail = DeliveryNoteDetailItem(
                product_id=detail.product_id,
                unit_conversions_id=detail.unit_conversions_id,
                quantity=detail.quantity,
                unit_price=detail.unit_price,
                vat=detail.vat
            )
            delivery_note_details.append(delivery_detail)

        # Create delivery note request
        delivery_note_request = CreateDeliveryNoteRequest(
            order_id=order_id,
            customer_id=data.customer_id,
            delivery_type=data.delivery_type,
            delivery_note_details=delivery_note_details
        )

        # Create delivery note
        delivery_note_response = await create_delivery_note_service(delivery_note_request, current_user)

        # Step 6: Reduce credit value after successful order completion
        credit_reduced = await reduce_credit_value_on_order_complete(current_user)
        if credit_reduced:
            logger.info(f"Successfully reduced credit value for user {current_user} after order completion")
        else:
            logger.warning(f"Failed to reduce credit value for user {current_user}, but order was created successfully")

        logger.info(f"Successfully created order {order_id} and delivery note {delivery_note_response.delivery_note_id} for user {current_user}")

        return CreateOrderResponse(
            status="success",
            detail="Đơn hàng và phiếu xuất đã được tạo thành công",
            order_id=order_id,
            order_code=order_code,
            delivery_note_id=delivery_note_response.delivery_note_id,
            delivery_note_code=delivery_note_response.delivery_note_code,
            customer_id=data.customer_id,
            total_items=len(data.order_details),
            total_temp=total_temp,
            total_vat=total_vat,
            total_after_vat=total_after_vat
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo đơn hàng: {str(e)}"
        )
