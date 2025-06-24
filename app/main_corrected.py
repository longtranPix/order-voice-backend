import os
import json
import base64
import logging
from tempfile import NamedTemporaryFile
from typing import Dict, Any, Optional, List

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from pydantic import BaseModel, validator
import bcrypt

from app.extractor import extract_info_from_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
TEABLE_BASE_URL = os.getenv("TEABLE_BASE_URL", "https://app.teable.io/api")
TEABLE_TOKEN = os.getenv("TEABLE_TOKEN")
TEABLE_TABLE_ID = os.getenv("TEABLE_TABLE_ID", "tblv9Ou1thzbETynKn1")
CREATE_INVOICE_URL = os.getenv("CREATE_INVOICE_URL", "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceWS/createInvoice")
GET_PDF_URL = os.getenv("GET_PDF_URL", "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceUtilsWS/getInvoiceRepresentationFile")

# Validate required environment variables
if not TEABLE_TOKEN:
    raise ValueError("TEABLE_TOKEN environment variable is required")

app = FastAPI(title="Order Voice Backend", version="1.0.0")

# CORS Configuration - specify allowed origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic Models with validation
class Account(BaseModel):
    username: str
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class SignUp(BaseModel):  # Fixed typo: was "SingUp"
    username: str
    password: str
    business_name: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v
    
    @validator('business_name')
    def validate_business_name(cls, v):
        if len(v) < 2:
            raise ValueError('Business name must be at least 2 characters')
        return v

class OrderDetail(BaseModel):
    product_name: str
    unit_price: float
    quantity: int
    vat: float
    temp_total: float
    final_total: float
    
    @validator('unit_price', 'quantity', 'vat', 'temp_total', 'final_total')
    def validate_positive_numbers(cls, v):
        if v < 0:
            raise ValueError('Value must be positive')
        return v
    
    @validator('vat')
    def validate_vat_range(cls, v):
        if v < 0 or v > 100:
            raise ValueError('VAT must be between 0 and 100')
        return v

class CreateOrderRequest(BaseModel):
    customer_name: str
    invoice_state: bool
    order_details: List[OrderDetail]
    order_table_id: str
    detail_table_id: str
    
    @validator('customer_name')
    def validate_customer_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Customer name must be at least 2 characters')
        return v.strip()

class InvoiceRequest(BaseModel):
    username: str
    order_id: str  # Simplified: removed confusion between order_table_id and record_order_id
    invoice_payload: Dict[str, Any]
    
    @validator('invoice_payload')
    def validate_invoice_payload(cls, v):
        # Validate required nested structure
        if 'generalInvoiceInfo' not in v:
            raise ValueError('invoice_payload must contain generalInvoiceInfo')
        if 'templateCode' not in v['generalInvoiceInfo']:
            raise ValueError('generalInvoiceInfo must contain templateCode')
        return v

# Utility Functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

async def get_http_client():
    """Dependency to get async HTTP client."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

def get_whisper_model():
    """Dependency to get Whisper model (lazy loading)."""
    if not hasattr(get_whisper_model, "_model"):
        get_whisper_model._model = WhisperModel("small", compute_type="int8", device="cpu")
    return get_whisper_model._model

async def handle_teable_api_call(
    client: httpx.AsyncClient, 
    method: str, 
    url: str, 
    **kwargs
) -> Dict[str, Any]:
    """Handle Teable API calls with proper error handling."""
    try:
        logger.info(f"Making {method} request to: {url}")
        response = await client.request(method, url, **kwargs)
        logger.info(f"Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            logger.debug(f"Response data: {response_data}")
        except Exception:
            response_data = {"raw_response": response.text}
            logger.warning(f"Could not parse JSON response: {response.text}")
        
        if 200 <= response.status_code < 300:
            return {
                "success": True, 
                "status_code": response.status_code, 
                "data": response_data
            }
        else:
            error_message = f"API call failed with status {response.status_code}"
            if isinstance(response_data, dict) and "message" in response_data:
                error_message += f": {response_data['message']}"
            logger.error(f"Error: {error_message}")
            return {
                "success": False, 
                "status_code": response.status_code, 
                "error": error_message, 
                "data": response_data
            }
    except httpx.RequestError as e:
        error_message = f"Network error during API call: {str(e)}"
        logger.error(error_message)
        return {
            "success": False, 
            "error": error_message, 
            "details": {
                "exception_type": type(e).__name__, 
                "exception_message": str(e)
            }
        }
    except Exception as e:
        error_message = f"Unexpected error during API call: {str(e)}"
        logger.error(error_message)
        return {
            "success": False, 
            "error": error_message, 
            "details": {
                "exception_type": type(e).__name__, 
                "exception_message": str(e)
            }
        }

async def create_table(
    client: httpx.AsyncClient, 
    base_id: str, 
    payload: dict
) -> Optional[str]:
    """Create a new table in Teable."""
    url = f"{TEABLE_BASE_URL}/base/{base_id}/table/"
    headers = {
        "Authorization": TEABLE_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 201:
            logger.error(f"Could not create table: {response.text}")
            return None
        return response.json()["id"]
    except Exception as e:
        logger.error(f"Error creating table: {str(e)}")
        return None

async def update_record(
    client: httpx.AsyncClient,
    table_id: str,
    record_id: str,
    update_fields: dict
) -> bool:
    """Update a record in Teable."""
    update_url = f"{TEABLE_BASE_URL}/table/{table_id}/record/{record_id}"
    headers = {
        "Authorization": TEABLE_TOKEN,
        "Content-Type": "application/json"
    }
    update_payload = {
        "fieldKeyType": "dbFieldName",
        "typecast": True,
        "record": {"fields": update_fields}
    }

    try:
        response = await client.patch(update_url, json=update_payload, headers=headers)
        logger.info(f"Update response status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error updating record: {str(e)}")
        return False

# API Endpoints
@app.post("/transcribe")
async def transcribe_and_extract(
    file: UploadFile = File(...),
    whisper_model = Depends(get_whisper_model)
):
    """Transcribe audio file and extract order information."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )

        with NamedTemporaryFile(suffix=".webm", delete=True) as temp_audio:
            content = await file.read()
            temp_audio.write(content)
            temp_audio.flush()

            segments, info = whisper_model.transcribe(
                temp_audio.name,
                beam_size=5,
                vad_filter=True
            )
            text_result = " ".join([segment.text.strip() for segment in segments])

        extracted_json = extract_info_from_text(text_result)

        return {
            "language": info.language,
            "transcription": text_result.strip(),
            "extracted": extracted_json
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in transcription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )

@app.post("/signin")
async def signin(
    account: Account,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Authenticate user with username and password."""
    try:
        teable_url = f"{TEABLE_BASE_URL}/table/{TEABLE_TABLE_ID}/record"
        headers = {"Authorization": TEABLE_TOKEN, "Accept": "application/json"}
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": account.username}
                ]
            })
        }

        result = await handle_teable_api_call("GET", teable_url, params=params, headers=headers)

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

        # Verify password (assuming passwords are hashed in database)
        stored_password = records[0]["fields"].get("password")
        if not stored_password or not verify_password(account.password, stored_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        return {
            "status": "success",
            "accessToken": TEABLE_TOKEN.replace("Bearer ", ""),
            "message": "Authentication successful",
            "record": records
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error: {str(e)}"
        )

@app.post("/create-order")
async def create_order(
    data: CreateOrderRequest,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Create a new order with details."""
    try:
        headers = {
            "Authorization": TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Calculate totals
        total_temp = sum(item.unit_price * item.quantity for item in data.order_details)
        total_vat = sum(item.unit_price * item.quantity * item.vat / 100 for item in data.order_details)
        total_after_vat = total_temp + total_vat

        # Create detail records first
        detail_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{"fields": d.dict()} for d in data.order_details]
        }
        detail_url = f"{TEABLE_BASE_URL}/table/{data.detail_table_id}/record"

        response_detail = await client.post(detail_url, json=detail_payload, headers=headers)
        if response_detail.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not create order details: {response_detail.text}"
            )

        detail_records = response_detail.json().get("records", [])
        detail_ids = [r["id"] for r in detail_records]

        # Create order record
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

        response_order = await client.post(order_url, json=order_payload, headers=headers)
        if response_order.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not create order: {response_order.text}"
            )

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
        logger.error(f"Unexpected error creating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error creating order: {str(e)}"
        )
