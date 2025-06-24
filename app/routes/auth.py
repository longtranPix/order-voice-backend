import httpx
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import Account, SignUp, AuthResponse
from app.services import TeableService
from app.utils import get_http_client, encode_credentials
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signin", response_model=AuthResponse)
async def signin(
    account: Account,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Authenticate user with username and password."""
    try:
        teable_service = TeableService()
        result = await teable_service.get_user_by_credentials(
            client, account.username, account.password
        )

        if not result["success"]:
            raise HTTPException(
                status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail=result.get("error", "Could not authenticate user")
            )

        records = result.get("data", {}).get("records", [])
        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid username or password"
            )

        return AuthResponse(
            status="success",
            accessToken=settings.TEABLE_TOKEN.replace("Bearer ", ""),
            message="Authentication successful",
            record=records
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error: {str(e)}"
        )

@router.post("/signup")
async def signup(
    account: SignUp,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Register a new user account."""
    try:
        teable_service = TeableService()
        
        # Check if username already exists
        check_result = await teable_service.get_user_by_username(client, account.username)
        if not check_result["success"]:
            return {
                "status": "error", 
                "message": f"Could not check existing account: {check_result['error']}", 
                "status_code": check_result.get("status_code")
            }
        
        if check_result["data"].get("records"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Account with this username already exists"
            )

        # Create user record
        response_account = await teable_service.create_user_record(
            client, account.username, account.password, account.business_name
        )
        if response_account.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Could not create account"
            )

        record_id = response_account.json()["records"][0]["id"]

        # Create space and base
        space_response = await teable_service.create_space(client, f"{account.username}_space")
        if space_response.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create workspace"
            )
        space_id = space_response.json()["id"]

        base_response = await teable_service.create_base(
            client, space_id, f"{account.username}_base", "📊"
        )
        if base_response.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create database"
            )
        base_id = base_response.json()["id"]

        # Create tables
        detail_table_id = await teable_service.create_table(client, base_id, {
            "name": "Chi Tiết Hoá Đơn",
            "dbTableName": "invoice_details",
            "description": "Chi tiết đơn hàng",
            "icon": "🧾",
            "fields": [
                {"type": "autoNumber", "name": "Số đơn hàng chi tiết", "dbFieldName": "number_order_detail"},
                {"type": "longText", "name": "Tên Hàng Hoá", "dbFieldName": "product_name"},
                {"type": "number", "name": "Đơn Giá", "dbFieldName": "unit_price"},
                {"type": "number", "name": "Số Lượng", "dbFieldName": "quantity"},
                {"type": "number", "name": "VAT", "dbFieldName": "vat"},
                {"type": "number", "name": "Tạm Tính", "dbFieldName": "temp_total"},
                {"type": "number", "name": "Thành Tiền", "dbFieldName": "final_total"}
            ],
            "fieldKeyType": "dbFieldName",
            "records": []
        })
        
        if not detail_table_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Could not create order details table"
            )

        order_table_id = await teable_service.create_table(client, base_id, {
            "name": "Đơn Hàng",
            "dbTableName": "orders",
            "description": "Bảng lưu thông tin các đơn hàng",
            "icon": "📦",
            "fields": [
                {"type": "autoNumber", "name": "Số đơn hàng", "dbFieldName": "order_number"},
                {"type": "longText", "name": "Tên Khách Hàng", "dbFieldName": "customer_name"},
                {"type": "link", "name": "Chi Tiết Hóa Đơn", "dbFieldName": "invoice_details", 
                 "options": {"foreignTableId": detail_table_id, "relationship": "oneMany"}},
                {"type": "checkbox", "name": "Xuất hoá đơn", "dbFieldName": "invoice_state"},
                {"type": "number", "name": "Tổng Tạm Tính", "dbFieldName": "total_temp"},
                {"type": "number", "name": "Tổng VAT", "dbFieldName": "total_vat"},
                {"type": "number", "name": "Tổng Sau VAT", "dbFieldName": "total_after_vat"},
                {"type": "singleLineText", "name": "Mã hoá đơn", "dbFieldName": "invoice_code"},
                {"type": "longText", "name": "Mã file xuất hoá đơn", "dbFieldName": "invoice_file_to_byte"},
            ],
            "fieldKeyType": "dbFieldName",
            "records": []
        })
        
        if not order_table_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Could not create orders table"
            )

        invoice_info_table_id = await teable_service.create_table(client, base_id, {
            "name": "Invoice Table",
            "dbTableName": "invoice_table",
            "description": "Bảng lưu thông tin hóa đơn",
            "icon": "🧾",
            "fields": [
                {"type": "singleLineText", "name": "Mã Hóa Đơn", "dbFieldName": "invoice_template", 
                 "description": "Trường mẫu chính", "unique": True},
                {"type": "singleLineText", "name": "Mã Mẫu", "dbFieldName": "template_code", 
                 "description": "Mã mẫu chính"},
                {"type": "multipleSelect", "name": "Sê-ri Hóa Đơn", "dbFieldName": "invoice_series", 
                 "description": "Nhiều sê-ri hóa đơn"}
            ],
            "fieldKeyType": "dbFieldName",
            "records": []
        })
        
        if not invoice_info_table_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Could not create invoice info table"
            )

        # Update user record with table IDs and encoded token
        encoded_str = encode_credentials(account.username, account.password)
        update_fields = {
            "table_order_detail_id": detail_table_id,
            "table_order_id": order_table_id,
            "table_invoice_info_id": invoice_info_table_id,
            "invoice_token": encoded_str
        }
        
        success = await teable_service.update_record(
            client, settings.TEABLE_TABLE_ID, record_id, update_fields
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Account created but could not update with table IDs"
            )

        return {
            "status": "success",
            "message": "Account, workspace, database and tables created successfully",
            "account_id": record_id,
            "table_order_id": order_table_id,
            "table_order_detail_id": detail_table_id,
            "table_invoice_info_id": invoice_info_table_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unexpected error during registration: {str(e)}"
        )
