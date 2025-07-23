"""
Import slip service for creating import slips
"""
import json
import logging
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.teable_service import handle_teable_api_call
from app.services.auth_service import get_user_table_info
from app.services.plan_status_service import reduce_credit_value_on_order_complete
from app.schemas.import_slips import CreateImportSlipRequest, ImportSlipResponse
from app.schemas.delivery_notes import CreateDeliveryNoteRequest, DeliveryNoteResponse

logger = logging.getLogger(__name__)



async def create_import_slip_service(data: CreateImportSlipRequest, current_user: str) -> ImportSlipResponse:
    """Create import slip with details"""
    try:
        # Step 1: Get user table information
        user_info = await get_user_table_info(current_user)
        
        # Extract required table IDs
        import_slip_details_table_id = user_info.get("table_import_slip_details_id")
        import_slip_table_id = user_info.get("table_import_slip_id")
        product_table_id = user_info.get("table_product_id")
        access_token = user_info.get("access_token")
        
        if not all([import_slip_details_table_id, import_slip_table_id, product_table_id, access_token]):
            missing_fields = []
            if not import_slip_details_table_id: missing_fields.append("table_import_slip_details_id")
            if not import_slip_table_id: missing_fields.append("table_import_slip_id")
            if not product_table_id: missing_fields.append("table_product_id")
            if not access_token: missing_fields.append("access_token")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Thiếu thông tin bảng cần thiết: {', '.join(missing_fields)}"
            )
        
        # Step 2: Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Step 3: Create import slip details first
        detail_records = []
        total_amount = 0.0
        
        for detail in data.import_slip_details:
            # Calculate amounts
            temp_total = detail.unit_price * detail.quantity
            vat_amount = temp_total * (detail.vat / 100)
            final_total = temp_total + vat_amount
            total_amount += final_total
            
            detail_record = {
                "fields": {
                    "product_link": [detail.product_id],  # Link to product table
                    "unit_conversions": [detail.unit_conversions_id],  # Link to unit conversions table
                    "quantity": detail.quantity,
                    "unit_price": detail.unit_price,
                    "vat": detail.vat,
                    "temp_total": temp_total,
                    "final_total": final_total
                }
            }
            detail_records.append(detail_record)
        
        # Create import slip details
        details_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": detail_records
        }
        
        details_url = f"{settings.TEABLE_BASE_URL}/table/{import_slip_details_table_id}/record"
        details_result = handle_teable_api_call("POST", details_url, data=json.dumps(details_payload), headers=headers)
        
        if not details_result["success"]:
            raise HTTPException(
                status_code=details_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo chi tiết phiếu nhập: {details_result.get('error', 'Unknown error')}"
            )
        
        # Get created detail record IDs
        detail_records_created = details_result.get("data", {}).get("records", [])
        detail_ids = [record["id"] for record in detail_records_created]
        
        # Step 4: Create main import slip
        import_slip_fields = {
            "import_slip_details": detail_ids,  # Link to created details
            "supplier_link": [data.supplier_id],  # Link to supplier table
            "import_type": data.import_type
        }
        
        import_slip_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": import_slip_fields
            }]
        }
        
        import_slip_url = f"{settings.TEABLE_BASE_URL}/table/{import_slip_table_id}/record"
        import_slip_result = handle_teable_api_call("POST", import_slip_url, data=json.dumps(import_slip_payload), headers=headers)
        
        if not import_slip_result["success"]:
            raise HTTPException(
                status_code=import_slip_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo phiếu nhập: {import_slip_result.get('error', 'Unknown error')}, import_slip_url: {import_slip_url}, import_slip_payload: {import_slip_payload}"
            )
        
        # Get created import slip info
        import_slip_record = import_slip_result.get("data", {}).get("records", [{}])[0]
        import_slip_id = import_slip_record.get("id", "")
        import_slip_code = import_slip_record.get("fields", {}).get("import_slip_code", "")
        
        # Reduce credit value after successful import slip creation
        credit_reduced = await reduce_credit_value_on_order_complete(current_user)
        if credit_reduced:
            logger.info(f"Successfully reduced credit value for user {current_user} after import slip creation")
        else:
            logger.warning(f"Failed to reduce credit value for user {current_user}, but import slip was created successfully")

        logger.info(f"Successfully created import slip {import_slip_id} for user {current_user}")

        return ImportSlipResponse(
            status="success",
            detail="Phiếu nhập đã được tạo thành công",
            import_slip_id=import_slip_id,
            import_slip_code=import_slip_code,
            import_slip_details_ids=detail_ids,
            total_items=len(data.import_slip_details),
            total_amount=total_amount
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating import slip: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo phiếu nhập: {str(e)}"
        )

async def create_delivery_note_service(data: CreateDeliveryNoteRequest, current_user: str) -> DeliveryNoteResponse:
    """Create delivery note with details and link to order"""
    try:
        # Step 1: Get user table information
        user_info = await get_user_table_info(current_user)

        # Extract required table IDs
        delivery_note_details_table_id = user_info.get("table_delivery_note_details_id")
        delivery_note_table_id = user_info.get("table_delivery_note_id")
        product_table_id = user_info.get("table_product_id")
        access_token = user_info.get("access_token")

        if not all([delivery_note_details_table_id, delivery_note_table_id, product_table_id, access_token]):
            missing_fields = []
            if not delivery_note_details_table_id: missing_fields.append("table_delivery_note_details_id")
            if not delivery_note_table_id: missing_fields.append("table_delivery_note_id")
            if not product_table_id: missing_fields.append("table_product_id")
            if not access_token: missing_fields.append("access_token")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Thiếu thông tin bảng cần thiết: {', '.join(missing_fields)}"
            )

        # Step 2: Prepare headers with user's access token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Step 3: Create delivery note details first
        detail_records = []

        for detail in data.delivery_note_details:

            detail_record = {
                "fields": {
                    "product_link": [detail.product_id],  # Link to product table
                    "quantity": detail.quantity
                }
            }

            # Add unit conversions link if provided
            if detail.unit_conversions_id:
                detail_record["fields"]["unit_conversions"] = [detail.unit_conversions_id]
            detail_records.append(detail_record)

        # Create delivery note details
        details_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": detail_records
        }

        details_url = f"{settings.TEABLE_BASE_URL}/table/{delivery_note_details_table_id}/record"
        details_result = handle_teable_api_call("POST", details_url, data=json.dumps(details_payload), headers=headers)

        if not details_result["success"]:
            raise HTTPException(
                status_code=details_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo chi tiết phiếu xuất: {details_result.get('error', 'Unknown error')}"
            )

        # Get created detail record IDs
        detail_records_created = details_result.get("data", {}).get("records", [])
        detail_ids = [record["id"] for record in detail_records_created]

        # Step 4: Create main delivery note
        delivery_note_fields = {
            "order_link": [data.order_id],  # Link to order
            "delivery_note_details": detail_ids,  # Link to created details
            "delivery_type": data.delivery_type
        }

        delivery_note_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": delivery_note_fields
            }]
        }

        delivery_note_url = f"{settings.TEABLE_BASE_URL}/table/{delivery_note_table_id}/record"
        delivery_note_result = handle_teable_api_call("POST", delivery_note_url, data=json.dumps(delivery_note_payload), headers=headers)

        if not delivery_note_result["success"]:
            raise HTTPException(
                status_code=delivery_note_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể tạo phiếu xuất: {delivery_note_result.get('error', 'Unknown error')}"
            )

        # Get created delivery note info
        delivery_note_record = delivery_note_result.get("data", {}).get("records", [{}])[0]
        delivery_note_id = delivery_note_record.get("id", "")
        delivery_note_code = delivery_note_record.get("fields", {}).get("delivery_note_code", "")

        logger.info(f"Successfully created delivery note {delivery_note_id} for order {data.order_id} by user {current_user}")

        return DeliveryNoteResponse(
            status="success",
            detail="Phiếu xuất đã được tạo thành công",
            delivery_note_id=delivery_note_id,
            delivery_note_code=delivery_note_code,
            delivery_note_details_ids=detail_ids,
            order_id=data.order_id,
            customer_id=data.customer_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating delivery note: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo phiếu xuất: {str(e)}"
        )
