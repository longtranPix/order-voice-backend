import json
import requests
import logging
from datetime import datetime
from fastapi import HTTPException, status
from app.core.config import settings
from app.constants.auth_data import TABLE_NAME_MAPPING, TEMPLATE_ID, VIETQR_BASE_URL
from app.schemas.profile import UpdateProfileRequest, UpdateProfileResponse
from app.utils.auth_utils import (
    encode_password, verify_password, create_invoice_token, 
    handle_teable_api_call, update_user_table_id
)
from app.schemas.auth import Account, SignUp

logger = logging.getLogger(__name__)

async def signin_service(account: Account) -> dict:
    """Handle user signin with password verification"""
    try:
        teable_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        headers = {"Authorization": settings.TEABLE_TOKEN, "Accept": "application/json"}
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": account.username}
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

        # Verify password
        user_record = records[0]
        stored_password = user_record.get("fields", {}).get("password", "")
        
        if not verify_password(account.password, account.username, stored_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên người dùng hoặc mật khẩu không hợp lệ"
            )

        # Update last_login field with current datetime
        record_id = user_record["id"]
        current_datetime = datetime.now().isoformat()

        update_fields = {
            "last_login": current_datetime
        }

        # Update the user record with last login time
        update_success = update_user_table_id(
            settings.TEABLE_TABLE_ID, 
            record_id, 
            update_fields, 
            settings.TEABLE_TOKEN, 
            settings.TEABLE_BASE_URL
        )
        if not update_success:
            # Log the error but don't fail the signin process
            logger.warning(f"Failed to update last_login for user {account.username}")

        # Get access token from user record
        access_token = user_record.get("fields", {}).get("access_token", "")
        if not access_token:
            # Fallback to invoice token if access token not available
            access_token = user_record.get("fields", {}).get("invoice_token", "")

        return {
            "status": "success",
            "accessToken": access_token,
            "detail": "Xác thực thành công",
            "record": records
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signin error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )

# async def generate_space_access_token(space_id: str, space_name: str, headers: dict) -> str:
#     """Generate access token for the created space"""
#     try:
#         # Login as admin to get session
#         login_data = {
#             "email": settings.TEABLE_ADMIN_EMAIL,
#             "password": settings.TEABLE_ADMIN_PASSWORD
#         }
        
#         login_response = requests.post(
#             f"{settings.TEABLE_BASE_URL}/auth/login",
#             data=json.dumps(login_data),
#             headers={"Content-Type": "application/json"}
#         )
        
#         if login_response.status_code != 200:
#             logger.error(f"Admin login failed: {login_response.text}")
#             return ""
        
#         session_token = login_response.json().get("accessToken", "")
#         if not session_token:
#             logger.error("No session token received from admin login")
#             return ""
        
#         # Generate access token for the space
#         token_headers = {
#             "Authorization": f"Bearer {session_token}",
#             "Content-Type": "application/json"
#         }
        
#         token_data = {
#             "spaceId": space_id,
#             "name": f"Access Token for {space_name}"
#         }
        
#         token_response = requests.post(
#             f"{settings.TEABLE_BASE_URL}/space/{space_id}/access-token",
#             data=json.dumps(token_data),
#             headers=token_headers
#         )
        
#         if token_response.status_code == 201:
#             return token_response.json().get("accessToken", "")
#         else:
#             logger.error(f"Token generation failed: {token_response.text}")
#             return ""
            
#     except Exception as e:
#         logger.error(f"Error generating access token: {str(e)}")
#         return ""

async def generate_space_access_token(space_id: str, space_name: str, headers: dict) -> str:
    """Generate access token for the created space"""
    try:
        # Step 1: Sign in to Teable to get session
        signin_url = f"{settings.TEABLE_BASE_URL}/auth/signin"
        signin_payload = {
            "email": settings.TEABLE_ADMIN_EMAIL,
            "password": settings.TEABLE_ADMIN_PASSWORD
        }
        
        signin_response = requests.post(signin_url, json=signin_payload, headers=headers)
        if signin_response.status_code != 200:
            logger.error(f"Failed to signin to Teable: {signin_response.text}")
            return ""
        
        # Get session cookie from signin response
        session_cookie = None
        if 'Set-Cookie' in signin_response.headers:
            cookies = signin_response.headers['Set-Cookie']
            # Extract auth_session cookie
            for cookie in cookies.split(','):
                if 'auth_session=' in cookie:
                    session_cookie = cookie.split(';')[0]
                    break
        
        # Step 2: Create access token for the space
        access_token_url = f"{settings.TEABLE_BASE_URL}/access-token"
        access_token_payload = {
            "name": f"token_basic_{space_name}",
            "description": f"Access token for space {space_name}",
            "scopes": [
                "space|create", "space|delete", "space|read", "space|update",
                "space|invite_email", "space|invite_link", "space|grant_role",
                "base|create", "base|delete", "base|read", "base|read_all", "base|update",
                "base|invite_email", "base|invite_link", "base|table_import", "base|table_export",
                "base|authority_matrix_config", "base|db_connection", "base|query_data",
                "table|create", "table|delete", "table|read", "table|update",
                "table|import", "table|export", "table|trash_read", "table|trash_update", "table|trash_reset",
                "view|create", "view|delete", "view|read", "view|update", "view|share",
                "record|create", "record|delete", "record|read", "record|update", "record|comment",
                "field|create", "field|delete", "field|read", "field|update",
                "automation|create", "automation|delete", "automation|read", "automation|update",
                "user|email_read", "table_record_history|read"
            ],
            "expiredTime": "2025-09-28",
            "spaceIds": [space_id],
            "baseIds": ["bseki4xHvepa4Rk69K9"],
            "hasFullAccess": True
        }
        
        # Add session cookie to headers
        token_headers = headers.copy()
        if session_cookie:
            token_headers['Cookie'] = session_cookie
        
        token_response = requests.post(access_token_url, json=access_token_payload, headers=token_headers)
        if token_response.status_code != 201:
            logger.error(f"Failed to create access token: {token_response.text}")
            return ""
        
        token_data = token_response.json()
        access_token = token_data.get("token", "")
        
        if access_token:
            logger.info(f"Successfully created access token for space {space_id}")
        else:
            logger.error(f"No token returned in response: {token_data}")
        
        return access_token
        
    except Exception as e:
        logger.error(f"Error generating space access token: {str(e)}")
        return ""

async def create_token_registry_record(username: str, access_token: str, headers: dict):
    """Create record in token registry table"""
    try:
        registry_payload = {
            "typecast": True,
            "records": [{
                "fields": {
                    "username": username,
                    "access_token": access_token,
                    "created_at": datetime.now().isoformat()
                }
            }],
            "fieldKeyType": "dbFieldName"
        }
        
        registry_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TOKEN_LIST_TABLE_ID}/record"
        result = handle_teable_api_call("POST", registry_url, data=json.dumps(registry_payload), headers=headers)
        
        if result["success"]:
            logger.info(f"Token registry record created for user: {username}")
        else:
            logger.error(f"Failed to create token registry record: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error creating token registry record: {str(e)}")

async def signup_service(account: SignUp) -> dict:
    """Handle user signup with comprehensive workspace creation"""
    try:
        # Step 1: Validate taxcode and get business information from VietQR API
        taxcode = account.username
        business_name = f"Shop_Basic_{account.username}"
        # vietqr_url = f"{VIETQR_BASE_URL}/{taxcode}"

        # try:
        #     vietqr_response = requests.get(vietqr_url)
        #     vietqr_response.raise_for_status()
        #     vietqr_data = vietqr_response.json()

        #     if vietqr_data.get("code") != "00":
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail="Mã số thuế không tồn tại hoặc không hợp lệ"
        #         )

        #     business_name = vietqr_data["data"]["name"]
        #     logger.info(f"Found business: {business_name} for taxcode: {taxcode}")

        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error calling VietQR API: {str(e)}")
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail="Không thể xác minh mã số thuế. Vui lòng thử lại sau"
        #     )
        # except HTTPException:
        #     raise
        # except Exception as e:
        #     logger.error(f"Unexpected error validating taxcode: {str(e)}")
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail="Lỗi không mong muốn khi xác minh mã số thuế"
        #     )

        # Step 2: Check if username already exists in Teable
        headers = {"Authorization": settings.TEABLE_TOKEN, "Accept": "application/json", "Content-Type": "application/json"}
        teable_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"

        params_check = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({"conjunction": "and", "filterSet": [{"fieldId": "username", "operator": "is", "value": account.username}]})
        }
        check_result = handle_teable_api_call("GET", teable_url, params=params_check, headers=headers)
        if not check_result["success"]:
            logger.error(f"Không thể kiểm tra tài khoản đã tồn tại: {check_result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể kiểm tra tài khoản đã tồn tại: {check_result['error']}"
            )
        if check_result["data"].get("records"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tài khoản với mã số thuế này đã tồn tại")

        # Step 3: Create user account with encoded password
        encoded_password = encode_password(account.password, taxcode)
        invoice_token = create_invoice_token(taxcode, account.password)

        create_user_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": {
                    "username": account.username,
                    "password": encoded_password,
                    "business_name": business_name,
                    "invoice_token": invoice_token
                }
            }]
        }
        
        user_result = handle_teable_api_call("POST", teable_url, data=json.dumps(create_user_payload), headers=headers)
        if not user_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Không thể tạo tài khoản: {user_result.get('error', 'Unknown error')}"
            )

        record_id = user_result["data"]["records"][0]["id"]

        # Step 4: Create Teable Space
        space_name = f"{business_name}_workspace"
        space_response = requests.post(
            f"{settings.TEABLE_BASE_URL}/space", 
            data=json.dumps({"name": space_name}), 
            headers=headers
        )
        if space_response.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Không thể tạo không gian làm việc: {space_response.text}"
            )
        space_id = space_response.json()["id"]

        # Step 5: Generate Access Token
        access_token = await generate_space_access_token(space_id, space_name, headers)

        # Create record in token registry table
        if access_token:
            await create_token_registry_record(taxcode, access_token, headers)

        # Step 6: Create Base from Template
        template_payload = {
            "spaceId": space_id,
            "templateId": TEMPLATE_ID,
            "withRecords": False
        }

        base_response = requests.post(
            f"{settings.TEABLE_BASE_URL}/base/create-from-template",
            data=json.dumps(template_payload),
            headers=headers
        )

        if base_response.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể tạo cơ sở dữ liệu từ template: {base_response.text}"
            )

        base_data = base_response.json()
        base_id = base_data["id"]

        # Step 7: Extract Table Information
        tables_response = requests.get(
            f"{settings.TEABLE_BASE_URL}/base/{base_id}/table",
            headers=headers
        )

        tables_data = tables_response.json()

        # Map table names to IDs based on template structure
        table_mapping = {}
        for table in tables_data:
            table_name = table["name"]
            table_id = table["id"]
            table_mapping[table_name] = table_id
            logger.info(f"Found table: {table_name} -> {table_id}")

        # Extract table IDs based on expected table names from template
        extracted_table_ids = {}
        for template_name, field_name in TABLE_NAME_MAPPING.items():
            if template_name in table_mapping:
                extracted_table_ids[field_name] = table_mapping[template_name]
                logger.info(f"Mapped {template_name} -> {field_name}: {table_mapping[template_name]}")
            else:
                logger.warning(f"Table '{template_name}' not found in template base")

        # Step 8: Update User Record
        update_fields = {
            "invoice_token": invoice_token,
            "access_token": access_token
        }

        # Add all extracted table IDs to update fields
        update_fields.update(extracted_table_ids)

        update_success = update_user_table_id(
            settings.TEABLE_TABLE_ID, 
            record_id, 
            update_fields, 
            settings.TEABLE_TOKEN, 
            settings.TEABLE_BASE_URL
        )
        
        if not update_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Tài khoản đã được tạo, nhưng không thể cập nhật với các ID bảng"
            )

        return {
            "status": "success",
            "detail": "Tài khoản, không gian, cơ sở dữ liệu và tất cả các bảng đã được tạo thành công",
            "account_id": record_id,
            "business_name": business_name,
            "taxcode": taxcode,
            "workspace": {
                "space_id": space_id,
                "base_id": base_id,
                "access_token": access_token
            },
            "tables": extracted_table_ids
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Lỗi không mong muốn trong quá trình đăng ký: {str(e)}"
        )

# async def update_user_profile_by_authorization(update_data: UpdateProfileRequest, current_user_id) -> UpdateProfileResponse:
    """
    Update user profile information by Authorization header with Teable token
    """
    logger.info(f"Updating user profile for user ID: {current_user_id}")
    try:
        # Prepare the API URL for update
        api_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record/{current_user_id}"
        
        # Prepare headers
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Build update payload - only include fields that have values (not None)
        update_fields = {}
        
        # Only add fields that are not None
        if update_data.business_name is not None:
            update_fields["business_name"] = update_data.business_name
        
        if update_data.tax_code is not None:
            update_fields["tax_code"] = update_data.tax_code
            
        if update_data.bank_name is not None:
            update_fields["bank_name"] = update_data.bank_name
            
        if update_data.bank_number is not None:
            update_fields["bank_number"] = update_data.bank_number
            
        if update_data.account_name is not None:
            update_fields["account_name"] = update_data.account_name
        
        # If no fields to update, get current profile and return it
        if not update_fields:
            # Get current user profile
            current_profile = await get_current_user_profile_by_id(current_user_id)
            return UpdateProfileResponse(
                status="success",
                message="Không có thông tin nào được cập nhật",
                data=current_profile
            )
        
        # Prepare update payload
        payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "record": {
                "fields": update_fields
            }
        }
        
        logger.info(f"Updating user profile for record ID: {current_user_id}")
        logger.info(f"Update fields: {update_fields}")
        
        # Make the API call
        response = requests.patch(api_url, headers=headers, data=json.dumps(payload))
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Teable API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lỗi khi cập nhật thông tin: {response.status_code}"
            )
        
        logger.info(f"Successfully updated user profile for record ID: {current_user_id}")

        # Get updated user profile
        updated_profile = await get_current_user_profile_by_id(current_user_id)

        return UpdateProfileResponse(
            status="success",
            message="Cập nhật thông tin thành công",
            data=updated_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_user_profile_by_token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ không mong muốn: {str(e)}"
        )