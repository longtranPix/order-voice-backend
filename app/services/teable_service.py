import json
import requests
import logging
import base64
import tempfile
import os
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

def handle_teable_api_call(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Handle Teable API calls with proper error handling and logging"""
    try:
        logger.info(f"Making {method} request to: {url}")
        response = requests.request(method, url, **kwargs)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            logger.info(f"Response data: {response_data}")
        except json.JSONDecodeError:
            response_data = {"raw_response": response.text}
            logger.warning(f"Không thể phân tích dữ liệu JSON: {response.text}")
        
        if 200 <= response.status_code < 300:
            return {"success": True, "status_code": response.status_code, "data": response_data}
        else:
            error_message = f"Gọi API thất bại với mã trạng thái {response.status_code} {response.reason}"
            if isinstance(response_data, dict) and "detail" in response_data:
                error_message += f": {response_data['detail']}"
            logger.error(f"Lỗi: {error_message}")
            logger.error(f"Phản hồi đầy đủ: {response_data}")
            return {"success": False, "status_code": response.status_code, "error": error_message, "detail": response_data}
    except requests.exceptions.RequestException as e:
        error_message = f"Lỗi mạng trong quá trình gọi API: {str(e)}"
        logger.error(error_message)
        return {"success": False, "error": error_message, "details": {"exception_type": type(e).__name__, "exception_message": str(e)}}
    except Exception as e:
        error_message = f"Lỗi không mong muốn trong quá trình gọi API: {str(e)}"
        logger.error(error_message)
        return {"success": False, "error": error_message, "details": {"exception_type": type(e).__name__, "exception_message": str(e)}}

def create_table(base_id: str, payload: dict, headers: dict) -> Optional[str]:
    """Create a table in Teable"""
    try:
        url = f"{settings.TEABLE_BASE_URL}/base/{base_id}/table/"
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code != 201:
            logger.error(f"Không thể tạo bảng: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Không thể tạo bảng: {str(e)}")
        return None
    return response.json()["id"]

def get_field_id_by_name(table_id: str, field_name: str, headers: dict) -> Optional[str]:
    """Get field ID by field name"""
    try:
        fields_url = f"{settings.TEABLE_BASE_URL}/table/{table_id}/field"
        response = requests.get(fields_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Không thể lấy thông tin field: {response.text}")
            return None

        fields = response.json()
        for field in fields:
            if field.get("dbFieldName") == field_name:
                return field.get("id", "")

        logger.error(f"Không tìm thấy field {field_name}")
        return None
    except Exception as e:
        logger.error(f"Lỗi khi lấy field ID: {str(e)}")
        return None

def add_field_to_table(table_id: str, field_payload: dict, headers: dict) -> Optional[str]:
    """Add a field to existing table"""
    try:
        field_url = f"{settings.TEABLE_BASE_URL}/table/{table_id}/field"
        response = requests.post(field_url, data=json.dumps(field_payload), headers=headers)

        if response.status_code != 201:
            logger.error(f"Không thể tạo field: {response.text}")
            return None

        field_id = response.json().get("id", "")
        logger.info(f"Successfully created field {field_id}")
        return field_id
    except Exception as e:
        logger.error(f"Lỗi khi tạo field: {str(e)}")
        return None

def update_user_table_id(table_order_id: str = settings.TEABLE_TABLE_ID, record_order_id: str = '', update_fields: dict = '') -> bool:
    """Update user table with new field values"""
    headers_teable = {
        "Authorization": f"{settings.TEABLE_TOKEN}",
        "Content-Type": "application/json"
    }
    update_url = f"{settings.TEABLE_BASE_URL}/table/{table_order_id}/record/{record_order_id}"
    update_payload = json.dumps({
        "fieldKeyType": "dbFieldName",
        "record": {"fields": update_fields}
    })
    try:
        response = requests.patch(update_url, data=update_payload, headers=headers_teable)
    except Exception as e:
        logger.error(f"Không thể cập nhật user table: {str(e)}")
        return False
    return response.status_code == 200

def upload_attachment_to_teable(field_id: str, record_id: str, table_id: str, file_to_bytes: str, file_name: str):
    """Upload attachment to Teable"""
    # Tạo file tạm từ base64
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(base64.b64decode(file_to_bytes))
        temp_file_path = temp_file.name
        print(f"✅ Đã tạo file tạm tại: {temp_file_path}")

    try:
        with open(temp_file_path, "rb") as f:
            files = {
                "file": (file_name, f, "application/pdf")
            }

            headers = {
                "Authorization": f"{settings.TEABLE_TOKEN}",
                "Accept": "application/json"
            }

            url = f"{settings.TEABLE_BASE_URL}/table/{table_id}/record/{record_id}/{field_id}/uploadAttachment"
            response = requests.post(url, headers=headers, files=files)
            response.raise_for_status()

            print("✅ Upload thành công.")
            return response.json()
    except Exception as e:
        print(f"❌ Lỗi khi upload: {e}")
        raise
    finally:
        # Luôn xóa file tạm
        try:
            os.remove(temp_file_path)
            print(f"🧹 Đã xoá file tạm: {temp_file_path}")
        except Exception as cleanup_error:
            print(f"⚠️ Không thể xoá file tạm: {cleanup_error}")
