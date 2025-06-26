import json
import requests
import base64
import logging
from datetime import datetime
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.teable_service import handle_teable_api_call, create_table, update_user_table_id
from app.schemas.auth import Account, SignUp

logger = logging.getLogger(__name__)

async def signin_service(account: Account) -> dict:
    """Handle user signin"""
    try:
        teable_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        headers = {"Authorization": settings.TEABLE_TOKEN, "Accept": "application/json"}
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": account.username},
                    {"fieldId": "password", "operator": "is", "value": account.password}
                ]
            })
        }

        result = handle_teable_api_call("GET", teable_url, params=params, headers=headers)

        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=result.get("error", "Không thể xác thực người dùng")
            )

        records = result.get("data", {}).get("records", [])
        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tên người dùng hoặc mật khẩu không hợp lệ"
            )

        # Update last_login field with current datetime
        user_record = records[0]
        record_id = user_record["id"]
        current_datetime = datetime.now().isoformat()

        update_fields = {
            "last_login": current_datetime
        }

        # Update the user record with last login time
        update_success = update_user_table_id(settings.TEABLE_TABLE_ID, record_id, update_fields)
        if not update_success:
            # Log the error but don't fail the signin process
            logger.warning(f"Failed to update last_login for user {account.username}")

        return {
            "status": "success",
            "accessToken": settings.TEABLE_TOKEN.replace("Bearer ", ""),
            "detail": "Xác thực thành công",
            "record": records
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )

async def signup_service(account: SignUp) -> dict:
    """Handle user signup"""
    try:
        # Step 1: Validate taxcode and get business information from VietQR API
        taxcode = account.username
        vietqr_url = f"https://api.vietqr.io/v2/business/{taxcode}"

        try:
            vietqr_response = requests.get(vietqr_url)
            vietqr_response.raise_for_status()
            vietqr_data = vietqr_response.json()

            if vietqr_data.get("code") != "00":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mã số thuế không tồn tại hoặc không hợp lệ"
                )

            business_name = vietqr_data["data"]["name"]
            logger.info(f"Found business: {business_name} for taxcode: {taxcode}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling VietQR API: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể xác minh mã số thuế. Vui lòng thử lại sau"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating taxcode: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi không mong muốn khi xác minh mã số thuế"
            )

        # Step 2: Check if username already exists in Teable
        headers = {"Authorization": settings.TEABLE_TOKEN, "Accept": "application/json", "Content-Type": "application/json"}
        teable_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"

        params_check = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({"conjunction": "and", "filterSet": [{"fieldId": "username", "operator": "is", "value": account.username}]})
        }
        check_result = handle_teable_api_call("GET", teable_url, params=params_check, headers=headers)
        if not check_result["success"]:
            return {"status": "error", "detail": f"Không thể kiểm tra tài khoản đã tồn tại: {check_result['error']}", "status_code": check_result.get("status_code")}
        if check_result["data"].get("records"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tài khoản với mã số thuế này đã tồn tại")

        # Step 3: Create user account with business_name from VietQR API
        create_user_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{"fields": {"username": account.username, "password": account.password, "business_name": business_name}}]
        }
        response_account = requests.post(teable_url, data=json.dumps(create_user_payload), headers=headers)
        if response_account.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tạo tài khoản")

        record_id = response_account.json()["records"][0]["id"]

        # Step 4: Create space and base with business name
        space_name = f"{business_name}_workspace"
        base_name = f"{business_name}_database"

        space_id = requests.post(f"{settings.TEABLE_BASE_URL}/space", data=json.dumps({"name": space_name}), headers=headers).json()["id"]
        base_id = requests.post(f"{settings.TEABLE_BASE_URL}/base", data=json.dumps({"spaceId": space_id, "name": base_name, "icon": "📊"}), headers=headers).json()["id"]

        # Create detail table
        detail_table_id = create_table(base_id, {"name": "Chi Tiết Hoá Đơn", "dbTableName": "invoice_details", "description": "Chi tiết đơn hàng", "icon": "🧾", "fields": [
            {"type": "autoNumber", "name": "Số đơn hàng chi tiết", "dbFieldName": "number_order_detail"},
            {"type": "longText", "name": "Tên Hàng Hoá", "dbFieldName": "product_name"},
            {"type": "number", "name": "Đơn Giá", "dbFieldName": "unit_price"},
            {"type": "number", "name": "Số Lượng", "dbFieldName": "quantity"},
            {"type": "number", "name": "VAT", "dbFieldName": "vat"},
            {"type": "number", "name": "Tạm Tính", "dbFieldName": "temp_total"},
            {"type": "number", "name": "Thành Tiền", "dbFieldName": "final_total"}
        ], "fieldKeyType": "dbFieldName", "records": []}, headers)
        if not detail_table_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tạo bảng chi tiết đơn hàng")

        # Create order table and get the invoice_file field ID
        order_table_payload = {"name": "Đơn Hàng", "dbTableName": "orders", "description": "Bảng lưu thông tin các đơn hàng", "icon": "📦", "fields": [
            {"type": "autoNumber", "name": "Số đơn hàng", "dbFieldName": "order_number"},
            {"type": "longText", "name": "Tên Khách Hàng", "dbFieldName": "customer_name"},
            {"type": "link", "name": "Chi Tiết Hóa Đơn", "dbFieldName": "invoice_details", "options": {"foreignTableId": detail_table_id, "relationship": "oneMany"}},
            {"type": "checkbox", "name": "Xuất hoá đơn", "dbFieldName": "invoice_state"},
            {"type": "number", "name": "Tổng Tạm Tính", "dbFieldName": "total_temp"},
            {"type": "number", "name": "Tổng VAT", "dbFieldName": "total_vat"},
            {"type": "number", "name": "Tổng Sau VAT", "dbFieldName": "total_after_vat"},
            {"type": "singleLineText", "name": "Mã hoá đơn", "dbFieldName": "invoice_code"},
            {"type": "attachment", "name": "File hoá đơn", "dbFieldName": "invoice_file"}
        ], "fieldKeyType": "dbFieldName", "records": []}

        # Create order table and get full response to extract field IDs
        order_table_url = f"{settings.TEABLE_BASE_URL}/base/{base_id}/table/"
        order_table_response = requests.post(order_table_url, data=json.dumps(order_table_payload), headers=headers)
        if order_table_response.status_code != 201:
            logger.error(f"Không thể tạo bảng đơn hàng: {order_table_response.text}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tạo bảng đơn hàng")

        order_table_data = order_table_response.json()
        order_table_id = order_table_data["id"]

        # Find the invoice_file field ID
        upload_file_id = None
        for field in order_table_data.get("fields", []):
            if field.get("dbFieldName") == "invoice_file":
                upload_file_id = field.get("id")
                break

        if not upload_file_id:
            logger.warning("Could not find invoice_file field ID in order table")
            upload_file_id = ""

        # Create invoice info table
        invoice_info_table_id = create_table(base_id, {
            "name": "Invoice Table",
            "dbTableName": "invoice_table",
            "description": "Bảng lưu thông tin hóa đơn",
            "icon": "🧾",
            "fields": [
                {"type": "singleLineText", "name": "Mã Hóa Đơn", "dbFieldName": "invoice_template", "description": "Trường mẫu chính", "unique": True},
                {"type": "singleLineText", "name": "Mã Mẫu", "dbFieldName": "template_code", "description": "Mã mẫu chính"},
                {"type": "multipleSelect", "name": "Sê-ri Hóa Đơn", "dbFieldName": "invoice_series", "description": "Nhiều sê-ri hóa đơn"}
            ],
            "fieldKeyType": "dbFieldName",
            "records": []
        }, headers)
        if not invoice_info_table_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tạo bảng mẫu hóa đơn")

        # Create invoice token
        raw_string = f"{account.username}:{account.password}"
        encoded_bytes = base64.b64encode(raw_string.encode("utf-8"))
        encoded_str = encoded_bytes.decode("utf-8")

        # Update user record with table IDs and upload file field ID
        update_fields = {
            "table_order_detail_id": detail_table_id,
            "table_order_id": order_table_id,
            "table_invoice_info_id": invoice_info_table_id,
            "invoice_token": encoded_str,
            "upload_file_id": upload_file_id
        }
        if not update_user_table_id(settings.TEABLE_TABLE_ID, record_id, update_fields):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Tài khoản đã được tạo, nhưng không thể cập nhật với các ID bảng")

        return {
            "status": "success",
            "detail": "Tài khoản, không gian, cơ sở dữ liệu và các bảng đã được tạo thành công",
            "account_id": record_id,
            "business_name": business_name,
            "taxcode": taxcode,
            "table_order_id": order_table_id,
            "table_order_detail_id": detail_table_id,
            "table_invoice_info_id": invoice_info_table_id,
            "upload_file_id": upload_file_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi không mong muốn trong quá trình đăng ký: {str(e)}")
