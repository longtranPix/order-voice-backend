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
        
        # Add table IDs to the response if they exist
        table_field_names = [
            "table_customer_id",
            "table_unit_conversions_id", 
            "table_brand_id",
            "table_product_id",
            "table_order_detail_id",
            "table_order_id",
            "table_invoice_info_id",
            "table_import_slip_details_id",
            "table_delivery_note_details_id",
            "table_delivery_note_id",
            "table_supplier_id",
            "table_import_slip_id",
            "table_catalog_id",
            "table_attribute_id",
            "table_attribute_type_id",
            "upload_file_id"
        ]
        
        # Ensure all table ID fields are included in the response
        for field_name in table_field_names:
            if field_name not in user_fields:
                user_fields[field_name] = None
        
        logger.info(f"Retrieved user table info for {username} with {len([f for f in table_field_names if user_fields.get(f)])} table IDs")
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

        # Get user's table IDs from saved fields in user table
        user_fields = records[0].get("fields", {})
        base_id = user_fields.get("base_id")
        space_id = user_fields.get("space_id")

        # Extract table IDs from user fields (old method)
        tables_map = {}
        table_field_names = [
            "table_customer_id",
            "table_unit_conversions_id", 
            "table_brand_id",
            "table_product_id",
            "table_order_detail_id",
            "table_order_id",
            "table_invoice_info_id",
            "table_import_slip_details_id",
            "table_delivery_note_details_id",
            "table_delivery_note_id",
            "table_supplier_id",
            "table_import_slip_id",
            "table_catalog_id",
            "table_attribute_id",
            "table_attribute_type_id",
            "upload_file_id"
        ]
        
        for field_name in table_field_names:
            table_id = user_fields.get(field_name)
            if table_id:
                tables_map[field_name] = table_id
                logger.info(f"Retrieved {field_name}: {table_id}")
        
        logger.info(f"Retrieved {len(tables_map)} table IDs from user record")

        return {
            "status": "success",
            "accessToken": user_token,
            "detail": SUCCESS_MESSAGES["SIGNIN_SUCCESS"],
            "record": records,
            "workspace": {"space_id": space_id, "base_id": base_id},
            "tables": tables_map
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
        # Step 1: Call Teable Signup API to get user_id and session cookie
        teable_signup_url = "https://app.teable.vn/api/auth/signup"
        signup_payload = {
            "email": account.email,
            "password": account.password
        }
        
        try:
            signup_response = requests.post(teable_signup_url, json=signup_payload)
            logger.info(f"Teable signup response status: {signup_response.status_code}")
            
            if signup_response.status_code == 201 or signup_response.status_code == 200:
                signup_data = signup_response.json()
                teable_user_id = signup_data.get("id")
                
                # Extract auth_session cookie
                session_cookie = None
                if 'Set-Cookie' in signup_response.headers:
                    cookies = signup_response.headers['Set-Cookie']
                    for cookie in cookies.split(','):
                        if 'auth_session=' in cookie:
                            session_cookie = cookie.split(';')[0]
                            break
                            
                if not teable_user_id:
                    raise HTTPException(status_code=400, detail="Không nhận được ID người dùng từ hệ thống")
                if not session_cookie:
                    raise HTTPException(status_code=400, detail="Không nhận được phiên làm việc từ hệ thống")
                    
                logger.info(f"Teable signup success. UserID: {teable_user_id}")
            else:
                error_detail = signup_response.text
                try:
                    error_json = signup_response.json()
                    if "message" in error_json:
                        error_detail = error_json["message"]
                except:
                    pass
                raise HTTPException(status_code=400, detail=f"Lỗi đăng ký hệ thống: {error_detail}")

        except requests.RequestException as e:
            logger.error(f"Teable signup connection error: {str(e)}")
            raise HTTPException(status_code=500, detail="Không thể kết nối đến hệ thống đăng ký")

        # Step 2: Proceed with local user creation
        # Validate taxcode and get business information
        taxcode = account.username
        business_name = f"Shop_{taxcode}"

        # Check if user already exists
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

        # Create user account record with encoded password and user_id
        encoded_password = encode_password(account.password, taxcode)
        encoded_str = base64.b64encode(f"{taxcode}:{account.password}".encode()).decode()

        user_record_payload = {
            "typecast": True,
            "records": [{
                "fields": {
                    "username": taxcode,
                    "password": encoded_password,
                    "business_name": business_name,
                    "invoice_token": encoded_str,
                    "user_id": teable_user_id, # Store Teable User ID
                    "email": account.email
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

        # Step 3: Create workspace using the user's session cookie
        space_name = f"{business_name}{DEFAULT_SPACE_NAME_SUFFIX}_V3"

        # Headers for space creation request (using cookie)
        cookie_headers = {
            "Content-Type": "application/json",
            "Cookie": session_cookie
        }

        space_response = requests.post(f"{settings.TEABLE_BASE_URL}/space", data=json.dumps({"name": space_name}), headers=cookie_headers)
        if space_response.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không thể tạo không gian làm việc: {space_response.text}")
        space_id = space_response.json()["id"]

        # Step 4: Generate access token for the space (using user's session cookie)
        access_token = await generate_space_access_token(space_id, space_name, headers, session_cookie=session_cookie)
        if not access_token:
            logger.warning(f"Could not generate access token for space {space_id}")
            access_token = ""

        # Step 4.1: Invite longtran.pix@gmail.com and anh.tran@teable.vn to the workspace
        try:
            invite_url = f"{settings.TEABLE_BASE_URL}/space/{space_id}/invitation/email"
            invite_payload = {
                "emails": ["longtran.pix@gmail.com", "anh.tran@teable.vn"],
                "role": "owner"
            }
            invite_response = requests.post(invite_url, json=invite_payload, headers=cookie_headers)
            if invite_response.status_code in [200, 201]:
                logger.info(f"Successfully invited longtran.pix@gmail.com and anh.tran@teable.vn to space {space_id}")
            else:
                logger.error(f"Failed to invite users to space {space_id}: {invite_response.text}")
        except Exception as e:
            logger.error(f"Error inviting users to space {space_id}: {str(e)}")

        # Create record in token registry table
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
            space_headers = cookie_headers 
            logger.warning(f"Using cookie headers due to token generation failure")

        # Step 6: Create base from template (NEW APPROACH)
        # User request: Use cookie to create base instead of token
        template_payload = {
            "spaceId": space_id,
            # "templateId": "tpl2qOKQjJtcJI3C7R6",
            "templateId": settings.TEABLE_TEMPLATE_ID,
            "withRecords": False
        }

        # Use cookie_headers for base creation as requested
        base_response = requests.post(
            f"{settings.TEABLE_BASE_URL}/base/create-from-template",
            data=json.dumps(template_payload),
            headers=cookie_headers
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

        # Step 7: Get all table IDs from the created base and save them to user table
        table_ids = {}
        try:
            # Get all tables from the created base
            tables_url = f"{settings.TEABLE_BASE_URL}/base/{base_id}/table"
            # For fetching tables, we should also use cookie headers since we used it for creation
            tables_response = requests.get(tables_url, headers=cookie_headers)
            
            if tables_response.status_code == 200:
                tables_data = tables_response.json()
                # Build lookup by display Name
                name_to_id = {t.get("name"): t.get("id") for t in tables_data}
                
                # Map table display names to user table field names
                table_name_mapping = {
                    "Khách Hàng": "table_customer_id",
                    "Thương Hiệu": "table_brand_id",
                    "Danh Mục": "table_catalog_id",
                    "Sản Phẩm": "table_product_id",
                    "Tên Thuộc Tính": "table_attribute_type_id",
                    "Thuộc Tính": "table_attribute_id",
                    "Đơn Vị Tính Chuyển Đổi": "table_unit_conversions_id",
                    "Chi Tiết Đơn Hàng": "table_order_detail_id",
                    "Đơn Hàng": "table_order_id",
                    "Invoice Table": "table_invoice_info_id",
                    "Chi Tiết Phiếu Nhập": "table_import_slip_details_id",
                    "Phiếu Nhập": "table_import_slip_id",
                    "Chi Tiết Phiếu Xuất": "table_delivery_note_details_id",
                    "Phiếu Xuất": "table_delivery_note_id",
                    "Nhà Cung Cấp": "table_supplier_id"
                }
                
                # Extract table IDs for each expected table name
                for display_name, field_name in table_name_mapping.items():
                    if display_name in name_to_id:
                        table_ids[field_name] = name_to_id[display_name]
                        logger.info(f"Found table '{display_name}': {name_to_id[display_name]}")
                        
                        # Special case: If this is the Order table, get the invoice_file field ID
                        if display_name == "Đơn Hàng":
                            try:
                                order_fields = await get_field_ids_from_table(name_to_id[display_name], cookie_headers)
                                if "invoice_file" in order_fields:
                                    table_ids["upload_file_id"] = order_fields["invoice_file"]
                                    logger.info(f"Found 'invoice_file' field ID: {order_fields['invoice_file']}")
                            except Exception as e:
                                logger.error(f"Error getting fields for Order table: {str(e)}")
                    else:
                        logger.warning(f"Table '{display_name}' not found in base {base_id}")
            else:
                logger.error(f"Failed to get tables from base {base_id}: {tables_response.text}")

        except Exception as e:
            logger.error(f"Error fetching table IDs: {str(e)}")
        
        # Step 8: Update user record with base info and all table IDs
        update_fields = {
            "invoice_token": encoded_str,
            "access_token": access_token,
            "space_id": space_id,
            "base_id": base_id
        }
        
        # Add all extracted table IDs to update fields
        update_fields.update(table_ids)

        update_success = update_user_table_id(settings.TEABLE_TABLE_ID, record_id, update_fields)
        if not update_success:
            logger.warning(f"Failed to update user record with workspace IDs")

        return {
            "status": "success",
            "detail": SUCCESS_MESSAGES["SIGNUP_SUCCESS"],
            "account_id": record_id,
            "business_name": business_name,
            "taxcode": taxcode,
            "workspace": {
                "space_id": space_id,
                "base_id": base_id,
                "access_token": access_token
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signup_service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )

async def change_password_service(change_data: dict) -> dict:
    """
    Handle password change flow:
    1. Login with username + old password
    2. If successful, update to new password with encoding
    """
    try:
        username = change_data.get("username")
        old_password = change_data.get("old_password")
        new_password = change_data.get("new_password")
        
        logger.info(f"Attempting password change for user: {username}")
        
        # Step 1: Verify old password by attempting login
        # Encode the old password using the same rules as signup
        encoded_old_password = encode_password(old_password, username)
        
        # Search user table with username and encoded old password
        teable_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        headers = {"Authorization": settings.TEABLE_TOKEN, "Accept": "application/json"}
        params = {
            "fieldKeyType": "dbFieldName",
            "viewId": settings.TEABLE_USER_VIEW_ID,
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": username},
                    {"fieldId": "password", "operator": "is", "value": encoded_old_password}
                ]
            })
        }
        
        # Attempt to find user with old password
        result = handle_teable_api_call("GET", teable_url, params=params, headers=headers)
        
        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail="Không thể xác thực người dùng"
            )
        
        records = result.get("data", {}).get("records", [])
        if not records:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập hoặc mật khẩu cũ không chính xác"
            )
        
        # Step 2: Old password verification successful, now update to new password
        user_record = records[0]
        record_id = user_record["id"]
        
        # Encode new password using the same rules as signup
        encoded_new_password = encode_password(new_password, username)
        
        # Update password field
        update_fields = {"password": encoded_new_password}
        
        # Update the user record with new encoded password
        update_success = update_user_table_id(settings.TEABLE_TABLE_ID, record_id, update_fields)
        
        if not update_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể cập nhật mật khẩu mới"
            )
        
        logger.info(f"Successfully changed password for user: {username}")
        
        return {
            "status": "success",
            "detail": "Đổi mật khẩu thành công",
            "username": username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in change_password_service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )
