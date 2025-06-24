import json
import httpx
from typing import Dict, Any
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class InvoiceService:
    """Service for handling invoice operations with Viettel API."""
    
    def __init__(self):
        self.create_invoice_url = settings.CREATE_INVOICE_URL
        self.get_pdf_url = settings.GET_PDF_URL
    
    async def generate_invoice(
        self,
        client: httpx.AsyncClient,
        username: str,
        invoice_token: str,
        invoice_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate invoice using Viettel API."""
        headers = {
            "Authorization": f"Basic {invoice_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Step 1: Create invoice
            create_response = await client.post(
                f"{self.create_invoice_url}/{username}", 
                json=invoice_payload, 
                headers=headers
            )
            create_response.raise_for_status()
            create_result = create_response.json()
            
            if not create_result.get("result"):
                return {
                    "success": False,
                    "error": "Could not create invoice"
                }
            
            result = create_result["result"]
            invoice_no = result["invoiceNo"]
            supplier_tax_code = result["supplierTaxCode"]
            template_code = invoice_payload["generalInvoiceInfo"]["templateCode"]
            
            # Step 2: Get PDF
            pdf_payload = {
                "supplierTaxCode": supplier_tax_code,
                "invoiceNo": invoice_no,
                "templateCode": template_code,
                "fileType": "pdf"
            }
            
            pdf_response = await client.post(
                self.get_pdf_url, 
                json=pdf_payload, 
                headers=headers
            )
            pdf_response.raise_for_status()
            pdf_result = pdf_response.json()
            
            file_to_bytes = pdf_result.get("fileToBytes")
            if not file_to_bytes:
                return {
                    "success": False,
                    "error": "Could not get PDF file"
                }
            
            return {
                "success": True,
                "invoice_no": invoice_no,
                "file_to_bytes": file_to_bytes,
                "file_name": pdf_result.get("fileName")
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during invoice generation: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            return {
                "success": False,
                "error": f"Invoice generation failed: {str(e)}"
            }
