"""
Authentication utility functions
"""
import json
import requests
import logging
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

async def get_field_ids_from_table(table_id: str, headers: dict) -> dict:
    """Get field IDs from table using the field API"""
    try:
        field_info_url = f"{settings.TEABLE_BASE_URL}/table/{table_id}/field"
        field_info_response = requests.get(field_info_url, headers=headers)
        if field_info_response.status_code != 200:
            logger.error(f"Could not get field info for {table_id}")
            return {}

        fields = field_info_response.json()
        field_map = {}

        # Response format: [{"dbFieldName": "<name>", "id": "<id>"}, ...]
        for field in fields:
            db_field_name = field.get("dbFieldName")
            field_id = field.get("id")
            if db_field_name and field_id:
                field_map[db_field_name] = field_id

        logger.info(f"Retrieved {len(field_map)} fields from table {table_id}: {list(field_map.keys())}")
        return field_map

    except Exception as e:
        logger.error(f"Error getting field IDs from {table_id}: {str(e)}")
        return {}

async def add_calculated_fields_to_details(table_id: str, table_type: str, headers: dict):
    """Add calculated fields to detail tables"""
    try:
        # Get field IDs from the table
        field_map = await get_field_ids_from_table(table_id, headers)
        
        unit_price_field_id = field_map.get("unit_price")
        quantity_field_id = field_map.get("quantity")
        vat_field_id = field_map.get("vat")
        
        if not all([unit_price_field_id, quantity_field_id, vat_field_id]):
            logger.error(f"Could not find required field IDs in {table_id}")
            return
        
        # Create calculated fields
        calculated_fields = [
            {
                "type": "formula",
                "options": {"expression": f"{{{unit_price_field_id}}} * {{{quantity_field_id}}}"},
                "dbFieldName": "temp_total",
                "name": "Tạm Tính"
            },
            {
                "type": "formula", 
                "options": {"expression": f"({{{unit_price_field_id}}} * {{{quantity_field_id}}}) * ({{{vat_field_id}}} / 100)"},
                "dbFieldName": "vat_amount",
                "name": "Tiền VAT"
            },
            {
                "type": "formula",
                "options": {"expression": f"({{{unit_price_field_id}}} * {{{quantity_field_id}}}) + (({{{unit_price_field_id}}} * {{{quantity_field_id}}}) * ({{{vat_field_id}}} / 100))"},
                "dbFieldName": "final_total", 
                "name": "Thành Tiền"
            }
        ]
        
        # Create the calculated fields
        field_url = f"{settings.TEABLE_BASE_URL}/table/{table_id}/field"
        for field_data in calculated_fields:
            field_response = requests.post(field_url, data=json.dumps(field_data), headers=headers)
            if field_response.status_code != 201:
                logger.error(f"Failed to create calculated field {field_data['name']} in {table_id}: {field_response.text}")
            else:
                logger.info(f"Successfully created calculated field {field_data['name']} in {table_id}")
                
    except Exception as e:
        logger.error(f"Error adding calculated fields to {table_id}: {str(e)}")

async def add_rollup_fields_to_main_table(main_table_id: str, details_table_id: str, table_type: str, headers: dict):
    """Add rollup fields to main tables"""
    try:
        # Get field IDs from details table
        details_field_map = await get_field_ids_from_table(details_table_id, headers)
        temp_total_field_id = details_field_map.get("temp_total")
        vat_amount_field_id = details_field_map.get("vat_amount") 
        final_total_field_id = details_field_map.get("final_total")
        
        # Get field IDs from main table
        main_field_map = await get_field_ids_from_table(main_table_id, headers)
        
        # Find the link field that connects to details
        link_field_id = None
        for field_name, field_id in main_field_map.items():
            if "chi_tiet" in field_name.lower() or "details" in field_name.lower():
                link_field_id = field_id
                break
        
        if not all([temp_total_field_id, vat_amount_field_id, final_total_field_id, link_field_id]):
            logger.error(f"Could not find required field IDs for rollup in {main_table_id}")
            return
        
        # Create rollup fields
        rollup_fields = [
            {
                "type": "rollup",
                "options": {"expression": "sum({values})"},
                "lookupOptions": {
                    "foreignTableId": details_table_id,
                    "linkFieldId": link_field_id,
                    "lookupFieldId": temp_total_field_id
                },
                "dbFieldName": "total_temp",
                "name": "Tổng Tạm Tính"
            },
            {
                "type": "rollup",
                "options": {"expression": "sum({values})"},
                "lookupOptions": {
                    "foreignTableId": details_table_id,
                    "linkFieldId": link_field_id,
                    "lookupFieldId": vat_amount_field_id
                },
                "dbFieldName": "total_vat",
                "name": "Tổng VAT"
            },
            {
                "type": "rollup",
                "options": {"expression": "sum({values})"},
                "lookupOptions": {
                    "foreignTableId": details_table_id,
                    "linkFieldId": link_field_id,
                    "lookupFieldId": final_total_field_id
                },
                "dbFieldName": "total_after_vat",
                "name": "Tổng Sau VAT"
            }
        ]
        
        # Create the rollup fields
        field_url = f"{settings.TEABLE_BASE_URL}/table/{main_table_id}/field"
        for field_data in rollup_fields:
            field_response = requests.post(field_url, data=json.dumps(field_data), headers=headers)
            if field_response.status_code != 201:
                logger.error(f"Failed to create rollup field {field_data['name']} in {main_table_id}: {field_response.text}")
            else:
                logger.info(f"Successfully created rollup field {field_data['name']} in {main_table_id}")
                
    except Exception as e:
        logger.error(f"Error adding rollup fields to {main_table_id}: {str(e)}")

async def add_customer_lookup_fields(table_id: str, customer_table_id: str, customer_link_field_name: str, headers: dict):
    """Add customer lookup fields to tables that link to customer"""
    try:
        # Get customer table field IDs
        customer_field_map = await get_field_ids_from_table(customer_table_id, headers)
        customer_fullname_field_id = customer_field_map.get("fullname")
        customer_phone_field_id = customer_field_map.get("phone_number")
        
        # Get the table field IDs to find the customer link field
        table_field_map = await get_field_ids_from_table(table_id, headers)
        customer_link_field_id = table_field_map.get(customer_link_field_name)
        
        if not all([customer_fullname_field_id, customer_phone_field_id, customer_link_field_id]):
            logger.error(f"Could not find required field IDs for customer lookup in {table_id}")
            return
        
        # Create lookup fields
        lookup_fields = [
            {
                "type": "lookup",
                "name": "Tên Khách Hàng",
                "dbFieldName": "customer_name",
                "lookupOptions": {
                    "foreignTableId": customer_table_id,
                    "linkFieldId": customer_link_field_id,
                    "lookupFieldId": customer_fullname_field_id
                }
            },
            {
                "type": "lookup",
                "name": "Số Điện Thoại KH",
                "dbFieldName": "customer_phone",
                "lookupOptions": {
                    "foreignTableId": customer_table_id,
                    "linkFieldId": customer_link_field_id,
                    "lookupFieldId": customer_phone_field_id
                }
            }
        ]
        
        # Create the lookup fields
        field_url = f"{settings.TEABLE_BASE_URL}/table/{table_id}/field"
        for field_data in lookup_fields:
            field_response = requests.post(field_url, data=json.dumps(field_data), headers=headers)
            if field_response.status_code != 201:
                logger.error(f"Failed to create lookup field {field_data['name']} in {table_id}: {field_response.text}")
            else:
                logger.info(f"Successfully created lookup field {field_data['name']} in {table_id}")
                
    except Exception as e:
        logger.error(f"Error adding customer lookup fields to {table_id}: {str(e)}")

async def add_inventory_tracking_fields_to_product(product_table_id: str, import_slip_details_id: str, delivery_note_details_id: str, headers: dict):
    """Add inventory tracking fields to product table"""
    try:
        # Get field IDs from import slip details table
        import_details_field_map = await get_field_ids_from_table(import_slip_details_id, headers)
        import_quantity_field_id = import_details_field_map.get("quantity_unit_default")
        
        # Get field IDs from delivery note details table
        delivery_details_field_map = await get_field_ids_from_table(delivery_note_details_id, headers)
        delivery_quantity_field_id = delivery_details_field_map.get("quantity_unit_default")
        
        # Get field IDs from product table to find the link fields that connect FROM product TO details tables
        product_field_map = await get_field_ids_from_table(product_table_id, headers)
        
        # Find the link field IDs in the PRODUCT table that link to the details tables
        # These are the reverse link fields with exact dbFieldNames
        import_details_link_field_id = product_field_map.get("Chi_Tiet_Phieu_Nhap")
        delivery_details_link_field_id = product_field_map.get("Chi_Tiet_Phieu_Xuat")
        
        if not all([import_quantity_field_id, import_details_link_field_id, delivery_quantity_field_id, delivery_details_link_field_id]):
            logger.error(f"Could not find required field IDs for inventory tracking")
            logger.error(f"Import fields: quantity={import_quantity_field_id}, link_field={import_details_link_field_id}")
            logger.error(f"Delivery fields: quantity={delivery_quantity_field_id}, link_field={delivery_details_link_field_id}")
            logger.error(f"Product field map: {list(product_field_map.keys())}")
            return
        
        # Create inventory tracking fields
        # Note: linkFieldId should be the field in the PRODUCT table that links to the details tables
        inventory_fields = [
            {
                "type": "rollup",
                "options": {"expression": "sum({values})"},
                "lookupOptions": {
                    "foreignTableId": import_slip_details_id,
                    "linkFieldId": import_details_link_field_id,  # Field in product table: "Chi_Tiet_Phieu_Nhap"
                    "lookupFieldId": import_quantity_field_id     # Field in import_slip_details to sum
                },
                "dbFieldName": "total_imported",
                "name": "Tổng nhập"
            },
            {
                "type": "rollup",
                "options": {"expression": "sum({values})"},
                "lookupOptions": {
                    "foreignTableId": delivery_note_details_id,
                    "linkFieldId": delivery_details_link_field_id,  # Field in product table: "Chi_Tiet_Phieu_Xuat"
                    "lookupFieldId": delivery_quantity_field_id     # Field in delivery_note_details to sum
                },
                "dbFieldName": "total_exported",
                "name": "Tổng xuất"
            }
        ]
        
        # Create the rollup fields first
        field_url = f"{settings.TEABLE_BASE_URL}/table/{product_table_id}/field"
        for field_data in inventory_fields:
            field_response = requests.post(field_url, data=json.dumps(field_data), headers=headers)
            if field_response.status_code != 201:
                logger.error(f"Failed to create inventory field {field_data['name']} in {product_table_id}: {field_response.text}")
        
        # Wait a moment for fields to be created, then get updated field map
        import time
        time.sleep(2)
        
        # Get updated field map to find the rollup field IDs
        product_field_map = await get_field_ids_from_table(product_table_id, headers)
        total_imported_field_id = product_field_map.get("total_imported")
        total_exported_field_id = product_field_map.get("total_exported")
        
        if not all([total_imported_field_id, total_exported_field_id]):
            logger.error(f"Could not find created rollup field IDs in product table")
            return
        
        # Create formula field for current stock (imported - exported)
        stock_formula_field = {
            "type": "formula",
            "options": {
                "expression": f"IF(BLANK({{{total_imported_field_id}}}), 0, {{{total_imported_field_id}}}) - IF(BLANK({{{total_exported_field_id}}}), 0, {{{total_exported_field_id}}})"
            },
            "dbFieldName": "inventory",
            "name": "Tồn kho hiện tại"
        }
        
        # Create the formula field
        formula_response = requests.post(field_url, data=json.dumps(stock_formula_field), headers=headers)
        if formula_response.status_code != 201:
            logger.error(f"Failed to create stock formula field in {product_table_id}: {formula_response.text}")
        else:
            logger.info(f"Successfully created inventory tracking fields in product table")
                
    except Exception as e:
        logger.error(f"Error adding inventory tracking fields to {product_table_id}: {str(e)}")

async def create_token_registry_record(username: str, access_token: str, headers: dict):
    """Create a record in the token registry table"""
    try:
        token_registry_table_id = settings.TEABLE_TOKEN_LIST_TABLE_ID
        
        # Create record payload
        record_payload = {
            "records": [
                {
                    "fields": {
                        "username": username,
                        "token": access_token
                    }
                }
            ],
            "fieldKeyType": "dbFieldName"
        }
        
        # Create record in token registry table
        registry_url = f"{settings.TEABLE_BASE_URL}/table/{token_registry_table_id}/record"
        registry_response = requests.post(registry_url, data=json.dumps(record_payload), headers=headers)
        
        if registry_response.status_code == 201:
            logger.info(f"Successfully created token registry record for user {username}")
            return True
        else:
            logger.error(f"Failed to create token registry record: {registry_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating token registry record for {username}: {str(e)}")
        return False

async def get_username_by_token(token: str) -> str:
    """Get username by token from token list table"""
    try:
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Query token list table to find username by token
        token_list_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TOKEN_LIST_TABLE_ID}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "token", "operator": "is", "value": token}
                ]
            })
        }
        
        response = requests.get(token_list_url, headers=headers, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to get token info: {response.text}")
            return ""
        
        data = response.json()
        records = data.get("records", [])
        
        if not records:
            logger.warning(f"No user found for token: {token[:20]}...")
            return ""
        
        # Get username from the first matching record
        username = records[0].get("fields", {}).get("username", "")
        if username:
            logger.info(f"Found username {username} for token")
            return username
        else:
            logger.warning(f"Username field not found in token record")
            return ""
            
    except Exception as e:
        logger.error(f"Error getting username by token: {str(e)}")
        return ""

async def get_token_by_username(username: str) -> str:
    """Get token by username from token list table"""
    try:
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Query token list table to find token by username
        token_list_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TOKEN_LIST_TABLE_ID}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": username}
                ]
            })
        }
        
        response = requests.get(token_list_url, headers=headers, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to get user token: {response.text}")
            return ""
        
        data = response.json()
        records = data.get("records", [])
        
        if not records:
            logger.warning(f"No token found for username: {username}")
            return ""
        
        # Get token from the first matching record
        token = records[0].get("fields", {}).get("token", "")
        if token:
            logger.info(f"Found token for username {username}")
            return token
        else:
            logger.warning(f"Token field not found in user record")
            return ""
            
    except Exception as e:
        logger.error(f"Error getting token by username: {str(e)}")
        return ""

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
            "name": f"token_{space_name}",
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
            "baseIds": None,
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
