import json
import requests
import logging
from fastapi import HTTPException
from app.core.config import settings
from app.services.teable_service import upload_attachment_to_teable, update_user_table_id
from app.schemas.invoices import InvoiceRequest

logger = logging.getLogger(__name__)

def generate_invoice_service(data: InvoiceRequest, current_user: str) -> dict:
    """Handle invoice generation"""
    # Step 1: Get user configuration including invoice_token and invoice config
    # Use current_user from token instead of data.username for security
    url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
    params = {
        "fieldKeyType": "dbFieldName",
        "filter": json.dumps({"conjunction":"and","filterSet":[{"fieldId":"username","operator":"is","value":f"{current_user}"}]})
    }

    try:
        teable_resp = requests.get(url, params, headers={"Authorization": settings.TEABLE_TOKEN, "Accept": "application/json"})
        teable_resp.raise_for_status()
        records = teable_resp.json().get("records", [])
        if not records:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản trong Teable")

        user_record = records[0]["fields"]
        invoice_token = user_record.get("invoice_token")
        if not invoice_token:
            raise HTTPException(status_code=400, detail="Không có invoice_token trong record")

        # Get invoice configuration field names and values
        invoice_type_fieldname = user_record.get("invoice_type_fieldname", "invoiceType")
        invoice_code_fieldname = user_record.get("invoice_code_fieldname", "templateCode")
        invoice_series_fieldname = user_record.get("invoice_series_fieldname", "invoiceSeries")

        invoice_type = user_record.get("invoice_type")
        template_code = user_record.get("template_code")
        invoice_series = user_record.get("invoice_series")

        # Get dynamic API URLs from user configuration with fallback to static config
        domain_api_invoice = user_record.get("domain_api_invoice") or settings.CREATE_INVOICE_URL
        domain_api_get_file = user_record.get("domain_api_get_file") or settings.GET_PDF_URL

        # Log which URLs are being used
        logger.info(f"Using invoice API: {domain_api_invoice}")
        logger.info(f"Using PDF API: {domain_api_get_file}")

        if not all([invoice_type, template_code, invoice_series]):
            raise HTTPException(status_code=400, detail="Thiếu thông tin cấu hình hóa đơn (invoice_type, template_code, invoice_series)")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thông tin cấu hình: {str(e)}")

    # Step 2: Prepare invoice payload with configuration values
    invoice_payload = data.invoice_payload.copy()

    # Ensure generalInvoiceInfo exists
    if "generalInvoiceInfo" not in invoice_payload:
        invoice_payload["generalInvoiceInfo"] = {}

    # Automatically populate invoice configuration fields
    invoice_payload["generalInvoiceInfo"][invoice_type_fieldname] = invoice_type
    invoice_payload["generalInvoiceInfo"][invoice_code_fieldname] = template_code
    invoice_payload["generalInvoiceInfo"][invoice_series_fieldname] = invoice_series

    # Step 3: Create invoice
    headers = {
        "Authorization": f"Basic {invoice_token}",
        "Content-Type": "application/json"
    }

    try:
        # Use dynamic invoice API URL from user configuration
        create_invoice_url = f"{domain_api_invoice}/{data.username}"
        create_response = requests.post(create_invoice_url, json=invoice_payload, headers=headers)
        create_response.raise_for_status()
        create_result = create_response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo hóa đơn: {str(e)}")

    if not create_result.get("result"):
        raise HTTPException(status_code=500, detail="Không tạo được hóa đơn")

    result = create_result["result"]
    invoice_no = result["invoiceNo"]
    supplier_tax_code = result["supplierTaxCode"]

    # Step 4: Get PDF
    pdf_payload = {
        "supplierTaxCode": supplier_tax_code,
        "invoiceNo": invoice_no,
        "templateCode": template_code,  # Use template_code from user configuration
        "fileType": "pdf"
    }

    try:
        # Use dynamic PDF API URL from user configuration
        pdf_response = requests.post(domain_api_get_file, json=pdf_payload, headers=headers)
        pdf_response.raise_for_status()
        pdf_result = pdf_response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy file PDF: {str(e)}")

    file_to_bytes = pdf_result.get("fileToBytes")
    filename = pdf_result.get("fileName")
    if not file_to_bytes:
        raise HTTPException(status_code=500, detail="Không lấy được file PDF")

    # Step 5: Update order in system
    upload_attachment_to_teable(data.field_attachment_id, data.record_order_id, data.order_table_id, file_to_bytes, filename)
    update_fields = {
        "invoice_code": invoice_no,
        "invoice_state": True
    }

    if not update_user_table_id(data.order_table_id, data.record_order_id, update_fields):
        raise HTTPException(
            status_code=500,
            detail="Tạo hóa đơn thành công nhưng cập nhật order thất bại."
        )

    return {
        "detail": "Hóa đơn đã tạo và cập nhật vào order thành công.",
        "invoice_no": invoice_no,
        "file_name": pdf_result.get("fileName")
    }
