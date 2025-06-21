from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from tempfile import NamedTemporaryFile
from app.extractor import extract_info_from_text
from pydantic import BaseModel
import json
import requests
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Teable API Configuration
TEABLE_BASE_URL = "https://app.teable.io/api"
TEABLE_TOKEN = "Bearer teable_accT1cTLbgDxAw73HQa_xnRuWiEDLat6qqpUDsL4QEzwnKwnkU9ErG7zgJKJswg="
TEABLE_TABLE_ID = "tblv9Ou1thzbETynKn1"

def handle_teable_api_call(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """
    Helper function to handle Teable API calls with detailed error reporting

    Args:
        method: HTTP method (GET, POST, etc.)
        url: API endpoint URL
        **kwargs: Additional arguments for requests

    Returns:
        Dict containing success status, data, and error details if any
    """
    try:
        logger.info(f"Making {method} request to: {url}")

        # Make the API call
        response = requests.request(method, url, **kwargs)

        # Log response details
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")

        # Try to parse JSON response
        try:
            response_data = response.json()
            logger.info(f"Response data: {response_data}")
        except json.JSONDecodeError:
            response_data = {"raw_response": response.text}
            logger.warning(f"Failed to parse JSON response: {response.text}")

        # Check if request was successful
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response_data
            }
        else:
            error_message = f"API call failed with status {response.status_code}"
            if isinstance(response_data, dict) and "message" in response_data:
                error_message += f": {response_data['message']}"

            logger.error(f"API Error: {error_message}")
            logger.error(f"Full response: {response_data}")

            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_message,
                "details": response_data
            }

    except requests.exceptions.RequestException as e:
        error_message = f"Network error during API call: {str(e)}"
        logger.error(error_message)
        return {
            "success": False,
            "error": error_message,
            "details": {"exception_type": type(e).__name__, "exception_message": str(e)}
        }
    except Exception as e:
        error_message = f"Unexpected error during API call: {str(e)}"
        logger.error(error_message)
        return {
            "success": False,
            "error": error_message,
            "details": {"exception_type": type(e).__name__, "exception_message": str(e)}
        }

# Cho phép CORS (giới hạn origin trong production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Giới hạn cụ thể trong production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request bodies
class Account(BaseModel):
    username: str
    password: str


# Load mô hình Faster-Whisper
whisper_model = WhisperModel("small", compute_type="int8", device="cpu")

@app.post("/transcribe/")
async def transcribe_and_extract(file: UploadFile = File(...)):
    try:
        # Ghi file tạm, sẽ tự xóa sau khi đóng
        with NamedTemporaryFile(suffix=".webm", delete=True) as temp_audio:
            temp_audio.write(await file.read())
            temp_audio.flush()

            # Chuyển giọng nói thành văn bản
            segments, info = whisper_model.transcribe(temp_audio.name, beam_size=5, language="vi", vad_filter=True)
            text_result = " ".join([segment.text.strip() for segment in segments])

        # Trích xuất thông tin từ văn bản
        extracted_json = extract_info_from_text(text_result)

        return {
            "language": info.language,
            "transcription": text_result.strip(),
            "extracted": extracted_json,
        }

    except Exception as e:
        return {
            "error": str(e)
        }

@app.post("/signin")
async def signin(account: Account):
    try:
        teable_url = f"{TEABLE_BASE_URL}/table/{TEABLE_TABLE_ID}/record"
        headers = {
            "Authorization": TEABLE_TOKEN,
            "Accept": "application/json"
        }
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

        # Make API call with detailed error handling
        result = handle_teable_api_call("GET", teable_url, params=params, headers=headers)

        if not result["success"]:
            return {
                "status": "error",
                "message": f"Failed to authenticate user: {result['error']}",
                "details": result.get("details", {}),
                "status_code": result.get("status_code")
            }

        data = result["data"]
        if data and data.get("records"):
            return {
                "status": "success",
                "accessToken": TEABLE_TOKEN.replace("Bearer ", ""),
                "message": "Authentication successful"
            }
        else:
            return {
                "status": "error",
                "message": "Invalid username or password",
                "details": {"records_found": len(data.get("records", []))}
            }
    except Exception as e:
        return {
            "error": str(e)
        }

@app.post("/signup")
async def signup(account: Account):
    try:
        teable_url = f"{TEABLE_BASE_URL}/table/{TEABLE_TABLE_ID}/record"
        headers = {
            "Authorization": TEABLE_TOKEN,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Step 1: Check if account exists
        params_check = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [{"fieldId": "username", "operator": "is", "value": account.username}]
            })
        }

        check_result = handle_teable_api_call("GET", teable_url, params=params_check, headers=headers)
        if not check_result["success"]:
            return {
                "status": "error",
                "message": f"Failed to check existing account: {check_result['error']}",
                "status_code": check_result.get("status_code")
            }

        if check_result["data"].get("records"):
            return {
                "status": "error",
                "message": "Account with this username already exists"
            }

        # Step 2: Create account
        payload_create_account = json.dumps({
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [
                {
                    "fields": {
                        "username": account.username,
                        "password": account.password
                    }
                }
            ]
        })
        response_account = requests.post(teable_url, data=payload_create_account, headers=headers)

        if response_account.status_code != 201:
            return {"status": "error", "message": "Failed to create account."}

        created_account = response_account.json()
        record_id = created_account["records"][0]["id"]

        # Step 3: Create space
        space_url = "https://app.teable.io/api/space"
        space_payload = json.dumps({"name": f"{account.username}_space"})
        response_space = requests.post(space_url, data=space_payload, headers=headers)
        if response_space.status_code != 201:
            return {"status": "error", "message": "Account created, but failed to create space."}
        space_id = response_space.json()["id"]

        # Step 4: Create base
        base_url = "https://app.teable.io/api/base"
        base_payload = json.dumps({"spaceId": space_id, "name": f"{account.username}_base", "icon": "📊"})
        response_base = requests.post(base_url, data=base_payload, headers=headers)
        if response_base.status_code != 201:
            return {"status": "error", "message": "Account created, but failed to create base."}
        base_id = response_base.json()["id"]

        # Step 5: Create table inside the base
        create_table_url = f"https://app.teable.io/api/base/{base_id}/table/"
        table_payload = json.dumps({
            "name": "Invoice Table",
            "dbTableName": "invoice_table",
            "description": "Table for invoices",
            "icon": "🧾",
            "fields": [
                {
                    "type": "singleLineText",
                    "name": "Invoice Code",
                    "dbFieldName": "invoice_template",
                    "description": "Main template field",
                    "unique": True
                },
                {
                    "type": "singleLineText",
                    "name": "Template Code",
                    "dbFieldName": "template_code",
                    "description": "Main template code",
                },
                {
                    "type": "multipleSelect",
                    "name": "Invoice Series",
                    "dbFieldName": "invoice_series",
                    "description": "Multiple invoice series"
                }
            ],
            "fieldKeyType": "dbFieldName"
        })
        response_table = requests.post(create_table_url, data=table_payload, headers=headers)
        if response_table.status_code != 201:
            return {"status": "error", "message": "Failed to create invoice table."}
        table_id = response_table.json()["id"]

        # Step 6: Update account record with table_id
        update_url = f"https://app.teable.io/api/table/{TEABLE_TABLE_ID}/record/{record_id}"
        update_payload = json.dumps({
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "record": {
                "fields": {
                    "table_id": table_id
                }
            }
        })

        response_update = requests.patch(update_url, data=update_payload, headers=headers)
        if response_update.status_code != 200:
            return {"status": "error", "message": "Account created, but failed to update with table ID."}

        return {
            "status": "success",
            "message": "Account, space, base, and table created successfully.",
            "account_id": record_id,
            "table_id": table_id
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Unexpected error",
            "error": str(e)
        }
