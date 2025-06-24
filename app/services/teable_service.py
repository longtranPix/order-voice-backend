import json
import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.orders import OrderDetail

logger = get_logger(__name__)

class TeableService:
    """Service for handling Teable API operations."""
    
    def __init__(self):
        self.base_url = settings.TEABLE_BASE_URL
        self.token = settings.TEABLE_TOKEN
        self.table_id = settings.TEABLE_TABLE_ID
        self.headers = {
            "Authorization": self.token,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def handle_api_call(
        self,
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
        self,
        client: httpx.AsyncClient,
        base_id: str,
        payload: dict
    ) -> Optional[str]:
        """Create a new table in Teable."""
        url = f"{self.base_url}/base/{base_id}/table/"

        try:
            response = await client.post(url, json=payload, headers=self.headers)
            if response.status_code != 201:
                logger.error(f"Could not create table: {response.text}")
                return None
            return response.json()["id"]
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            return None

    async def update_record(
        self,
        client: httpx.AsyncClient,
        table_id: str,
        record_id: str,
        update_fields: dict
    ) -> bool:
        """Update a record in Teable."""
        update_url = f"{self.base_url}/table/{table_id}/record/{record_id}"
        update_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "record": {"fields": update_fields}
        }

        try:
            response = await client.patch(update_url, json=update_payload, headers=self.headers)
            logger.info(f"Update response status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error updating record: {str(e)}")
            return False
    
    async def get_user_by_credentials(
        self,
        client: httpx.AsyncClient,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """Get user record by username and password."""
        url = f"{self.base_url}/table/{self.table_id}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": username},
                    {"fieldId": "password", "operator": "is", "value": password}
                ]
            })
        }
        return await self.handle_api_call(client, "GET", url, params=params, headers=self.headers)

    async def get_user_by_username(
        self,
        client: httpx.AsyncClient,
        username: str
    ) -> Dict[str, Any]:
        """Get user record by username only."""
        url = f"{self.base_url}/table/{self.table_id}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "filterSet": [
                    {"fieldId": "username", "operator": "is", "value": username}
                ]
            })
        }
        return await self.handle_api_call(client, "GET", url, params=params, headers=self.headers)
    
    async def create_user_record(
        self,
        client: httpx.AsyncClient,
        username: str,
        password: str,
        business_name: str
    ) -> httpx.Response:
        """Create a new user record."""
        url = f"{self.base_url}/table/{self.table_id}/record"
        payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": {
                    "username": username,
                    "password": password,
                    "business_name": business_name
                }
            }]
        }
        return await client.post(url, json=payload, headers=self.headers)

    async def create_space(self, client: httpx.AsyncClient, name: str) -> httpx.Response:
        """Create a new space."""
        url = f"{self.base_url}/space"
        payload = {"name": name}
        return await client.post(url, json=payload, headers=self.headers)

    async def create_base(
        self,
        client: httpx.AsyncClient,
        space_id: str,
        name: str,
        icon: str = "📊"
    ) -> httpx.Response:
        """Create a new base."""
        url = f"{self.base_url}/base"
        payload = {
            "spaceId": space_id,
            "name": name,
            "icon": icon
        }
        return await client.post(url, json=payload, headers=self.headers)
    
    async def create_order_records(
        self,
        client: httpx.AsyncClient,
        order_table_id: str,
        detail_table_id: str,
        customer_name: str,
        order_details: List[OrderDetail],
        invoice_state: bool
    ) -> Dict[str, Any]:
        """Create order and detail records."""
        # Calculate totals
        total_temp = sum(item.unit_price * item.quantity for item in order_details)
        total_vat = sum(item.unit_price * item.quantity * item.vat / 100 for item in order_details)
        total_after_vat = total_temp + total_vat

        # Create detail records first
        detail_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{"fields": d.model_dump()} for d in order_details]
        }
        detail_url = f"{self.base_url}/table/{detail_table_id}/record"
        response_detail = await client.post(detail_url, json=detail_payload, headers=self.headers)

        if response_detail.status_code != 201:
            return {
                "success": False,
                "error": f"Could not create order details: {response_detail.text}"
            }

        detail_records = response_detail.json().get("records", [])
        detail_ids = [r["id"] for r in detail_records]

        # Create order record
        order_payload = {
            "fieldKeyType": "dbFieldName",
            "typecast": True,
            "records": [{
                "fields": {
                    "customer_name": customer_name,
                    "invoice_details": detail_ids,
                    "total_temp": total_temp,
                    "total_vat": total_vat,
                    "total_after_vat": total_after_vat,
                    "invoice_state": invoice_state
                }
            }]
        }
        order_url = f"{self.base_url}/table/{order_table_id}/record"
        response_order = await client.post(order_url, json=order_payload, headers=self.headers)

        if response_order.status_code != 201:
            return {
                "success": False,
                "error": f"Could not create order: {response_order.text}"
            }

        return {
            "success": True,
            "order": response_order.json(),
            "total_temp": total_temp,
            "total_vat": total_vat,
            "total_after_vat": total_after_vat,
            "invoice_state": invoice_state
        }
