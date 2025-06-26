import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Teable API Configuration
    TEABLE_BASE_URL: str = os.getenv("TEABLE_BASE_URL", "https://app.teable.io/api")
    TEABLE_TOKEN: str = os.getenv("TEABLE_TOKEN", "Bearer teable_accT1cTLbgDxAw73HQa_xnRuWiEDLat6qqpUDsL4QEzwnKwnkU9ErG7zgJKJswg=")
    TEABLE_TABLE_ID: str = os.getenv("TEABLE_TABLE_ID", "tblv9Ou1thzbETynKn1")
    
    # Invoice API Configuration
    CREATE_INVOICE_URL: str = os.getenv("CREATE_INVOICE_URL", "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceWS/createInvoice")
    GET_PDF_URL: str = os.getenv("GET_PDF_URL", "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceUtilsWS/getInvoiceRepresentationFile")
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "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")
    
    # Server Configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

settings = Settings()
