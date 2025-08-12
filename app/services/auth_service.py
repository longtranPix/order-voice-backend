"""
Authentication service for user signup and signin flows only
"""
import json
import requests
import base64
import hashlib
import hmac
import logging
from datetime import datetime
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.teable_service import handle_teable_api_call, create_table, update_user_table_id, get_field_id_by_name, add_field_to_table
from app.schemas.auth import Account, SignUp
from app.utils.auth_utils import (
    get_field_ids_from_table,
    add_calculated_fields_to_details,
    add_rollup_fields_to_main_table,
    add_customer_lookup_fields,
    add_supplier_lookup_fields,
    add_product_lookup_fields,
    add_inventory_tracking_fields_to_product,
    create_token_registry_record,
    get_username_by_token,
    get_token_by_username,
    generate_space_access_token
)
from app.constants.auth_data import (
    CUSTOMER_TABLE_PAYLOAD,
    get_order_detail_table_payload,
    get_order_table_payload,
    INVOICE_INFO_TABLE_PAYLOAD,
    UNIT_CONVERSION_TABLE_PAYLOAD,
    get_product_table_payload,
    get_import_slip_details_payload,
    get_delivery_note_details_payload,
    get_delivery_note_payload,
    get_brand_table_payload,
    SUPPLIER_TABLE_PAYLOAD,
    get_import_slip_payload,
    VIETQR_API_BASE_URL,
    DEFAULT_SPACE_NAME_SUFFIX,
    DEFAULT_BASE_NAME_SUFFIX,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES
)

logger = logging.getLogger(__name__)

def encode_password(password: str, username: str) -> str:
    """
    Encode password using private rules for secure storage

    Private encoding rules:
    1. Combine password with username as salt
    2. Apply HMAC-SHA256 with secret key
    3. Add timestamp-based rotation
    4. Base64 encode final result
    """
    try:
        # Private rule 1: Create salt from username with rotation
        salt = f"{username}_CUBABLE_2025_{len(password)}"

        # Private rule 2: Create secret key from multiple sources
        secret_key = f"CUBABLE_SECRET_{username[:3]}_{len(username)}_ORDER_VOICE_2025"

        # Private rule 3: Combine password with salt and apply transformations
        combined = f"{password}:{salt}:{len(password + username)}"

        # Private rule 4: Apply HMAC-SHA256 with secret key
        encoded_bytes = hmac.new(
            secret_key.encode('utf-8'),
            combined.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Private rule 5: Add additional layer with base64 and custom suffix
        final_encoded = base64.b64encode(encoded_bytes).decode('utf-8')

        # Private rule 6: Add custom prefix and suffix for identification
        result = f"CUBABLE_{final_encoded}_PWD"

        logger.info(f"Password encoded successfully for user: {username}")
        return result

    except Exception as e:
        logger.error(f"Error encoding password for user {username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi mã hóa mật khẩu"
        )

def verify_password(plain_password: str, encoded_password: str, username: str) -> bool:
    """
    Verify password against encoded version using the same private rules
    """
    try:
        # Re-encode the plain password using the same rules
        re_encoded = encode_password(plain_password, username)

        # Compare with stored encoded password
        is_valid = hmac.compare_digest(re_encoded, encoded_password)

        logger.info(f"Password verification for user {username}: {'SUCCESS' if is_valid else 'FAILED'}")
        return is_valid

    except Exception as e:
        logger.error(f"Error verifying password for user {username}: {str(e)}")
        return False

async def get_user_table_info(username: str) -> dict:
    """Get user table information using viewId"""
    try:
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Get user table info with specific viewId
        user_table_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "viewId": settings.TEABLE_USER_VIEW_ID,
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": username}
                ]
            })
        }

        result = handle_teable_api_call("GET", user_table_url, params=params, headers=headers)

        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=f"Không thể lấy thông tin người dùng: {result.get('error', 'Unknown error')}"
            )

        records = result.get("data", {}).get("records", [])
        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông tin người dùng"
            )

        user_fields = records[0].get("fields", {})
        logger.info(f"Retrieved user table info for {username}")
        return user_fields

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user table info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin người dùng: {str(e)}"
        )

async def hide_reverse_link_fields_in_product_table(product_table_id: str, headers: dict):
    """Hide reverse link fields in product table to clean up the view"""
    try:
        # Get all fields from product table to find the reverse link field IDs
        fields_url = f"{settings.TEABLE_BASE_URL}/table/{product_table_id}/field"
        fields_result = handle_teable_api_call("GET", fields_url, headers=headers)

        if not fields_result["success"]:
            logger.warning(f"Could not get product table fields: {fields_result.get('error', 'Unknown error')}")
            return

        fields = fields_result.get("data", [])
        fields_to_hide = []

        # Find reverse link fields (these are auto-created by bidirectional relationships)
        for field in fields:
            field_name = field.get("name", "")
            field_type = field.get("type", "")
            field_id = field.get("id", "")

            # Hide fields that link back to import slip details and delivery note details
            if (field_type == "link" and
                ("Chi Tiết Phiếu Nhập" in field_name or
                 "Chi Tiết Phiếu Xuất" in field_name or
                 "import_slip_details" in field_name.lower() or
                 "delivery_note_details" in field_name.lower())):
                fields_to_hide.append({
                    "fieldId": field_id,
                    "columnMeta": {"hidden": True}
                })
                logger.info(f"Marking field '{field_name}' ({field_id}) for hiding")

        if not fields_to_hide:
            logger.info("No reverse link fields found to hide in product table")
            return

        # Get the default view ID for the product table
        views_url = f"{settings.TEABLE_BASE_URL}/table/{product_table_id}/view"
        views_result = handle_teable_api_call("GET", views_url, headers=headers)

        if not views_result["success"]:
            logger.warning(f"Could not get product table views: {views_result.get('error', 'Unknown error')}")
            return

        views = views_result.get("data", [])
        if not views:
            logger.warning("No views found in product table")
            return

        # Use the first view (usually the default view)
        default_view_id = views[0].get("id", "")
        if not default_view_id:
            logger.warning("Could not get default view ID for product table")
            return

        # Hide the fields in the default view
        hide_url = f"{settings.TEABLE_BASE_URL}/table/{product_table_id}/view/{default_view_id}/column-meta"
        hide_result = handle_teable_api_call("PUT", hide_url, data=json.dumps(fields_to_hide), headers=headers)

        if hide_result["success"]:
            logger.info(f"Successfully hid {len(fields_to_hide)} reverse link fields in product table")
        else:
            logger.warning(f"Failed to hide fields in product table: {hide_result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Error hiding reverse link fields in product table: {str(e)}")

async def add_conversion_fields_to_details(details_table_id: str, unit_conversion_table_id: str, headers: dict):
    """Add lookup and formula fields to import/delivery note details tables"""
    try:
        # Get field IDs
        unit_conversions_field_id = get_field_id_by_name(details_table_id, "unit_conversions", headers)
        conversion_factor_field_id = get_field_id_by_name(unit_conversion_table_id, "conversion_factor", headers)
        quantity_field_id = get_field_id_by_name(details_table_id, "quantity", headers)

        if not all([unit_conversions_field_id, conversion_factor_field_id, quantity_field_id]):
            logger.error("Không thể lấy field IDs cần thiết")
            return

        # Create lookup field for conversion factor
        lookup_field_payload = {
            "type": "number",
            "name": "Hệ số chuyển đổi",
            "dbFieldName": "conversion_factor_lookup",
            "isLookup": True,
            "lookupOptions": {
                "foreignTableId": unit_conversion_table_id,
                "linkFieldId": unit_conversions_field_id,
                "lookupFieldId": conversion_factor_field_id
            }
        }

        lookup_field_id = add_field_to_table(details_table_id, lookup_field_payload, headers)

        if lookup_field_id:
            # Create formula field for quantity in default unit
            formula_field_payload = {
                "type": "formula",
                "name": "Số lượng đơn vị mặc định",
                "dbFieldName": "quantity_unit_default",
                "options": {
                    "expression": f"{{{lookup_field_id}}} * {{{quantity_field_id}}}"
                }
            }

            formula_field_id = add_field_to_table(details_table_id, formula_field_payload, headers)

            if formula_field_id:
                logger.info(f"Successfully added conversion fields to table {details_table_id}")
            else:
                logger.error(f"Failed to create formula field for table {details_table_id}")
        else:
            logger.error(f"Failed to create lookup field for table {details_table_id}")

    except Exception as e:
        logger.error(f"Error adding conversion fields: {str(e)}")

async def signin_service(account: Account) -> dict:
    """Handle user signin flow with password encoding"""
    try:
        # Step 1: Encode the input password using the same rules as signup
        encoded_password = encode_password(account.password, account.username)

        # Step 2: Search user table with username and encoded password
        teable_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        headers = {"Authorization": settings.TEABLE_TOKEN, "Accept": "application/json"}
        params = {
            "fieldKeyType": "dbFieldName",
            "viewId": settings.TEABLE_USER_VIEW_ID,
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": account.username},
                    {"fieldId": "password", "operator": "is", "value": encoded_password}
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
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES["INVALID_CREDENTIALS"]
            )

        # Update last login time
        record_id = records[0]["id"]
        current_time = datetime.now().isoformat()
        update_fields = {"last_login": current_time}
        
        update_success = update_user_table_id(settings.TEABLE_TABLE_ID, record_id, update_fields)
        if not update_success:
            logger.warning(f"Failed to update last_login for user {account.username}")

        # Get user's space token from token list table
        user_token = await get_token_by_username(account.username)
        if not user_token:
            logger.warning(f"No space token found for user {account.username}, using main token")
            user_token = settings.TEABLE_TOKEN.replace("Bearer ", "")

        return {
            "status": "success",
            "accessToken": user_token,
            "detail": SUCCESS_MESSAGES["SIGNIN_SUCCESS"],
            "record": records
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signin_service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )

async def signup_service(account: SignUp) -> dict:
    """Handle user signup flow"""
    try:
        # Step 1: Validate taxcode and get business information from VietQR API
        taxcode = account.username
        business_name = f"Shop_{taxcode}"
        # vietqr_url = f"{VIETQR_API_BASE_URL}/{taxcode}"
        
        # try:
        #     vietqr_response = requests.get(vietqr_url, timeout=10)
        #     if vietqr_response.status_code != 200:
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail=ERROR_MESSAGES["INVALID_TAXCODE"]
        #         )
            
        #     vietqr_data = vietqr_response.json()
        #     business_name = vietqr_data.get("data", {}).get("name", "")
        #     if not business_name:
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail=ERROR_MESSAGES["INVALID_TAXCODE"]
        #         )
        # except requests.RequestException:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=ERROR_MESSAGES["INVALID_TAXCODE"]
        #     )

        # Step 2: Check if user already exists
        existing_user_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        check_params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [{"fieldId": "username", "operator": "is", "value": taxcode}]
            })
        }
        
        existing_result = handle_teable_api_call("GET", existing_user_url, params=check_params, headers=headers)
        if existing_result["success"] and len(existing_result.get("data", {}).get("records")) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES["USER_EXISTS"]
            )

        # Step 3: Create user account record with encoded password
        # Encode password using private rules before storing
        encoded_password = encode_password(account.password, taxcode)

        # Create invoice token (separate from password encoding)
        encoded_str = base64.b64encode(f"{taxcode}:{account.password}".encode()).decode()

        user_record_payload = {
            "typecast": True,
            "records": [{
                "fields": {
                    "username": taxcode,
                    "password": encoded_password,  # Store encoded password
                    "business_name": business_name,
                    "invoice_token": encoded_str
                }
            }],
            "fieldKeyType": "dbFieldName"
        }
        
        user_result = handle_teable_api_call("POST", existing_user_url, data=json.dumps(user_record_payload), headers=headers)
        if not user_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể tạo tài khoản người dùng: {user_result['error']}"
            )
        
        record_id = user_result["data"]["records"][0]["id"]

        # Step 4: Create space
        space_name = f"{business_name}{DEFAULT_SPACE_NAME_SUFFIX}"

        space_response = requests.post(f"{settings.TEABLE_BASE_URL}/space", data=json.dumps({"name": space_name}), headers=headers)
        if space_response.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không thể tạo không gian làm việc: {space_response.text}")
        space_id = space_response.json()["id"]

        # Step 4.1: Generate access token immediately after space creation
        access_token = await generate_space_access_token(space_id, space_name, headers)
        if not access_token:
            logger.warning(f"Could not generate access token for space {space_id}")
            access_token = ""

        # Step 4.1.1: Create record in token registry table
        if access_token:
            await create_token_registry_record(taxcode, access_token, headers)
        else:
            logger.warning(f"Skipping token registry record creation due to missing access token")

        # Step 4.2: Update headers to use the new space access token for all subsequent operations
        if access_token:
            space_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            logger.info(f"Switching to space access token for all subsequent operations")
        else:
            space_headers = headers  # Fallback to original headers if token generation failed
            logger.warning(f"Using fallback headers due to token generation failure")

        # Step 4.3: Create base from template (NEW APPROACH)
        template_payload = {
            "spaceId": space_id,
            "templateId": "tpl2qOKQjJtcJI3C7R6",
            "withRecords": False
        }

        base_response = requests.post(
            f"{settings.TEABLE_BASE_URL}/base/create-from-template",
            data=json.dumps(template_payload),
            headers=space_headers
        )

        if base_response.status_code != 201:
            logger.error(f"Failed to create base from template: {base_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể tạo cơ sở dữ liệu từ template: {base_response.text}"
            )

        base_data = base_response.json()
        base_id = base_data["id"]
        logger.info(f"Successfully created base from template: {base_id}")

        # Step 5: Get all table information from the created base (NEW APPROACH)
        tables_response = requests.get(
            f"{settings.TEABLE_BASE_URL}/base/{base_id}/table",
            headers=space_headers
        )

        if tables_response.status_code != 200:
            logger.error(f"Failed to get tables from base: {tables_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể lấy thông tin bảng từ cơ sở dữ liệu: {tables_response.text}"
            )

        tables_data = tables_response.json()
        logger.info(f"Retrieved {len(tables_data)} tables from base {base_id}")

        # Step 6: Map table names to IDs based on template structure
        table_mapping = {}
        for table in tables_data:
            table_name = table["name"]
            table_id = table["id"]
            table_mapping[table_name] = table_id
            logger.info(f"Found table: {table_name} -> {table_id}")

        # Step 7: Extract table IDs based on expected table names from template
        # Map template table names to our field names in user table
        table_name_mapping = {
            "Khách Hàng": "table_customer_id",
            "Đơn Vị Tính Chuyển Đổi": "table_unit_conversions_id",
            "Thương Hiệu": "table_brand_id",
            "Sản Phẩm": "table_product_id",
            "Chi Tiết Đơn Hàng": "table_order_detail_id",
            "Đơn Hàng": "table_order_id",
            "Thông Tin Hóa Đơn": "table_invoice_info_id",
            "Chi Tiết Phiếu Nhập": "table_import_slip_details_id",
            "Chi Tiết Phiếu Xuất": "table_delivery_note_details_id",
            "Phiếu Xuất": "table_delivery_note_id",
            "Nhà Cung Cấp": "table_supplier_id",
            "Phiếu Nhập": "table_import_slip_id",
            "Danh Mục": "table_catalog_id",
            "Ngành Hàng": "table_product_line_id",
            "Thuộc Tính": "table_attribute_id",
            "Tên Thuộc Tính": "table_attribute_type_id"
        }

        # Extract table IDs
        extracted_table_ids = {}
        for template_name, field_name in table_name_mapping.items():
            if template_name in table_mapping:
                extracted_table_ids[field_name] = table_mapping[template_name]
                logger.info(f"Mapped {template_name} -> {field_name}: {table_mapping[template_name]}")
            else:
                logger.warning(f"Table '{template_name}' not found in template base")

        # Step 8: Get upload file field ID from order table
        order_table_id = extracted_table_ids.get("table_order_id", "")
        upload_file_id = ""
        if order_table_id:
            try:
                order_field_map = await get_field_ids_from_table(order_table_id, space_headers)
                upload_file_id = order_field_map.get("invoice_file", "")
                logger.info(f"Found upload file field ID: {upload_file_id}")
            except Exception as e:
                logger.warning(f"Could not get upload file field ID: {str(e)}")
                upload_file_id = ""

        # Step 9: Update user record with all table IDs and access token
        update_fields = {
            "invoice_token": encoded_str,
            "upload_file_id": upload_file_id,
            "access_token": access_token
        }

        # Add all extracted table IDs to update fields
        update_fields.update(extracted_table_ids)

        update_success = update_user_table_id(settings.TEABLE_TABLE_ID, record_id, update_fields)
        if not update_success:
            logger.warning(f"Failed to update user record with table IDs")

        return {
            "status": "success",
            "detail": SUCCESS_MESSAGES["SIGNUP_SUCCESS"],
            "account_id": record_id,
            "business_name": business_name,
            "taxcode": taxcode,
            "workspace": {
                "space_id": space_id,
                "base_id": base_id,
                "access_token": access_token[:20] + "..." if access_token else "Not generated"
            },
            "tables": extracted_table_ids,
            "upload_file_id": upload_file_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signup_service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )
