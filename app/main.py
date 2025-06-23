from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from tempfile import NamedTemporaryFile
from app.extractor import extract_info_from_text
from pydantic import BaseModel
import json
import requests
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Teable API Configuration
TEABLE_BASE_URL = "https://app.teable.io/api"
TEABLE_TOKEN = "Bearer teable_accT1cTLbgDxAw73HQa_xnRuWiEDLat6qqpUDsL4QEzwnKwnkU9ErG7zgJKJswg="
TEABLE_TABLE_ID = "tblv9Ou1thzbETynKn1"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Account(BaseModel):
    username: str
    password: str
    business_name: str

class OrderDetail(BaseModel):
    product_name: str
    unit_price: float
    quantity: int
    vat: float
    temp_total: float
    final_total: float

class CreateOrderRequest(BaseModel):
    customer_name: str
    invoice_state: bool
    order_details: List[OrderDetail]
    order_table_id: str
    detail_table_id: str

def handle_teable_api_call(method: str, url: str, **kwargs) -> Dict[str, Any]:
    try:
        logger.info(f"Making {method} request to: {url}")
        response = requests.request(method, url, **kwargs)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        try:
            response_data = response.json()
            logger.info(f"Response data: {response_data}")
        except json.JSONDecodeError:
            response_data = {"raw_response": response.text}
            logger.warning(f"Failed to parse JSON response: {response.text}")
        if 200 <= response.status_code < 300:
            return {"success": True, "status_code": response.status_code, "data": response_data}
        else:
            error_message = f"API call failed with status {response.status_code}"
            if isinstance(response_data, dict) and "message" in response_data:
                error_message += f": {response_data['message']}"
            logger.error(f"API Error: {error_message}")
            logger.error(f"Full response: {response_data}")
            return {"success": False, "status_code": response.status_code, "error": error_message, "details": response_data}
    except requests.exceptions.RequestException as e:
        error_message = f"Network error during API call: {str(e)}"
        logger.error(error_message)
        return {"success": False, "error": error_message, "details": {"exception_type": type(e).__name__, "exception_message": str(e)}}
    except Exception as e:
        error_message = f"Unexpected error during API call: {str(e)}"
        logger.error(error_message)
        return {"success": False, "error": error_message, "details": {"exception_type": type(e).__name__, "exception_message": str(e)}}

def create_table(base_id: str, payload: dict, headers: dict) -> Optional[str]:
    url = f"{TEABLE_BASE_URL}/base/{base_id}/table/"
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    if response.status_code != 201:
        logger.error(f"Failed to create table: {response.text}")
        return None
    return response.json()["id"]

def update_user_table_id(record_id: str, update_fields: dict, headers: dict) -> bool:
    update_url = f"{TEABLE_BASE_URL}/table/{TEABLE_TABLE_ID}/record/{record_id}"
    update_payload = json.dumps({
        "fieldKeyType": "dbFieldName",
        "typecast": True,
        "record": {"fields": update_fields}
    })
    response = requests.patch(update_url, data=update_payload, headers=headers)
    return response.status_code == 200

whisper_model = WhisperModel("small", compute_type="int8", device="cpu")

@app.post("/transcribe/")
async def transcribe_and_extract(file: UploadFile = File(...)):
    try:
        with NamedTemporaryFile(suffix=".webm", delete=True) as temp_audio:
            temp_audio.write(await file.read())
            temp_audio.flush()
            segments, info = whisper_model.transcribe(temp_audio.name, beam_size=5, vad_filter=True)
            text_result = " ".join([segment.text.strip() for segment in segments])
        extracted_json = extract_info_from_text(text_result)
        return {"language": info.language, "transcription": text_result.strip(), "extracted": extracted_json}
    except Exception as e:
        return {"error": str(e)}

@app.post("/signin")
async def signin(account: Account):
    try:
        teable_url = f"{TEABLE_BASE_URL}/table/{TEABLE_TABLE_ID}/record"
        headers = {"Authorization": TEABLE_TOKEN, "Accept": "application/json"}
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
                detail=result.get("error", "Failed to authenticate user")
            )

        records = result.get("data", {}).get("records", [])
        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid username or password"
            )

        return {
            "status": "success",
            "accessToken": TEABLE_TOKEN.replace("Bearer ", ""),
            "message": "Authentication successful",
            "record": records
        }

    except HTTPException:
        raise  # Bảo toàn status code gốc

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error: {str(e)}"
        )


@app.post("/create-order")
async def create_order(data: CreateOrderRequest):
    try:
        headers = {
            "Authorization": TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        total_temp = sum(item.unit_price * item.quantity for item in data.order_details)
        total_vat = sum(item.unit_price * item.quantity * item.vat / 100 for item in data.order_details)
        total_after_vat = total_temp + total_vat

        detail_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{"fields": d.dict()} for d in data.order_details]
        }
        detail_url = f"{TEABLE_BASE_URL}/table/{data.detail_table_id}/record"
        response_detail = requests.post(detail_url, data=json.dumps(detail_payload), headers=headers)
        if response_detail.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create order details: {response_detail.text}")

        detail_records = response_detail.json().get("records", [])
        detail_ids = [r["id"] for r in detail_records]

        order_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": {
                    "customer_name": data.customer_name,
                    "invoice_details": detail_ids,
                    "total_temp": total_temp,
                    "total_vat": total_vat,
                    "total_after_vat": total_after_vat,
                    "invoice_state": data.invoice_state
                }
            }]
        }
        order_url = f"{TEABLE_BASE_URL}/table/{data.order_table_id}/record"
        response_order = requests.post(order_url, data=json.dumps(order_payload), headers=headers)
        if response_order.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create order: {response_order.text}")

        return {
            "status": "success",
            "order": response_order.json(),
            "total_temp": total_temp,
            "total_vat": total_vat,
            "total_after_vat": total_after_vat,
            "invoice_state": data.invoice_state
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error while creating order: {str(e)}")


@app.post("/signup")
async def signup(account: Account):
    try:
        headers = {"Authorization": TEABLE_TOKEN, "Accept": "application/json", "Content-Type": "application/json"}
        teable_url = f"{TEABLE_BASE_URL}/table/{TEABLE_TABLE_ID}/record"

        params_check = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({"conjunction": "and", "filterSet": [{"fieldId": "username", "operator": "is", "value": account.username}]})
        }
        check_result = handle_teable_api_call("GET", teable_url, params=params_check, headers=headers)
        if not check_result["success"]:
            return {"status": "error", "message": f"Failed to check existing account: {check_result['error']}", "status_code": check_result.get("status_code")}
        if check_result["data"].get("records"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account with this username already exists")

        create_user_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{"fields": {"username": account.username, "password": account.password, "business_name": account.business_name}}]
        }
        response_account = requests.post(teable_url, data=json.dumps(create_user_payload), headers=headers)
        if response_account.status_code != 201:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create account.")
        record_id = response_account.json()["records"][0]["id"]

        space_id = requests.post(f"{TEABLE_BASE_URL}/space", data=json.dumps({"name": f"{account.username}_space"}), headers=headers).json()["id"]
        base_id = requests.post(f"{TEABLE_BASE_URL}/base", data=json.dumps({"spaceId": space_id, "name": f"{account.username}_base", "icon": "📊"}), headers=headers).json()["id"]

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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create order detail table.")

        order_table_id = create_table(base_id, {"name": "Đơn Hàng", "dbTableName": "orders", "description": "Bảng lưu thông tin các đơn hàng", "icon": "📦", "fields": [
            {"type": "autoNumber", "name": "Số đơn hàng", "dbFieldName": "order_number"},
            {"type": "longText", "name": "Tên Khách Hàng", "dbFieldName": "customer_name"},
            {"type": "link", "name": "Chi Tiết Hóa Đơn", "dbFieldName": "invoice_details", "options": {"foreignTableId": detail_table_id, "relationship": "oneMany"}},
            {"type": "checkbox", "name": "Xuất hoá đơn", "dbFieldName": "invoice_state"},
            {"type": "number", "name": "Tổng Tạm Tính", "dbFieldName": "total_temp"},
            {"type": "number", "name": "Tổng VAT", "dbFieldName": "total_vat"},
            {"type": "number", "name": "Tổng Sau VAT", "dbFieldName": "total_after_vat"},
            {"type": "singleLineText", "name": "Mã hoá đơn", "dbFieldName": "invoice_code"}
        ], "fieldKeyType": "dbFieldName", "records": []}, headers)
        if not order_table_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create order table.")

        invoice_info_table_id = create_table(base_id, {
            "name": "Invoice Table",
            "dbTableName": "invoice_table",
            "description": "Table for invoices",
            "icon": "🧾",
            "fields": [
                {"type": "singleLineText", "name": "Invoice Code", "dbFieldName": "invoice_template", "description": "Main template field", "unique": True},
                {"type": "singleLineText", "name": "Template Code", "dbFieldName": "template_code", "description": "Main template code"},
                {"type": "multipleSelect", "name": "Invoice Series", "dbFieldName": "invoice_series", "description": "Multiple invoice series"}
            ],
            "fieldKeyType": "dbFieldName",
            "records": []
        }, headers)
        if not invoice_info_table_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create invoice template table.")

        update_fields = {
            "table_order_detail_id": detail_table_id,
            "table_order_id": order_table_id,
            "table_invoice_info_id": invoice_info_table_id
        }
        if not update_user_table_id(record_id, update_fields, headers):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Account created, but failed to update with table IDs.")

        return {
            "status": "success",
            "message": "Account, space, base, and tables created successfully.",
            "account_id": record_id,
            "table_order_id": order_table_id,
            "table_order_detail_id": detail_table_id,
            "table_invoice_info_id": invoice_info_table_id
        }


    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error during signup: {str(e)}")

