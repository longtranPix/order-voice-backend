async def signup_service(account: SignUp) -> dict:
    """Handle user signup flow"""
    try:
        # Step 1: Validate taxcode and get business information from VietQR API
        taxcode = account.username
        business_name = f"Shop_{taxcode}"

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