import os
from dotenv import load_dotenv

# Load environment variables from .env file with override
load_dotenv(override=True)

class Settings:
    # Teable API Configuration
    TEABLE_BASE_URL: str = os.getenv("TEABLE_BASE_URL", "https://app.teable.vn/api")
    TEABLE_TOKEN: str = os.getenv("TEABLE_TOKEN", "Bearer teable_accAFr0SCGDTUqXQTQb_+7LBL2ZrQJH/EN6utEyKq057Q0SEfVVFqrn0iDAu9aw=")
    TEABLE_TABLE_ID: str = os.getenv("TEABLE_TABLE_ID", "tblj52nsIFcIWDAW4fr")
    TEABLE_USER_VIEW_ID: str = os.getenv("TEABLE_USER_VIEW_ID", "viwWOH429ek2bW3eU06")
    TEABLE_TOKEN_LIST_TABLE_ID: str = os.getenv("TEABLE_TOKEN_LIST_TABLE_ID", "tblR7dckuSizsZlhW47")
    
    # Invoice API Configuration (Fallback URLs - now using dynamic URLs from user config)
    CREATE_INVOICE_URL: str = os.getenv("CREATE_INVOICE_URL", "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceWS/createInvoice")
    GET_PDF_URL: str = os.getenv("GET_PDF_URL", "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceUtilsWS/getInvoiceRepresentationFile")
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "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")

    # Teable Admin Credentials for Access Token Generation
    TEABLE_ADMIN_EMAIL: str = os.getenv("TEABLE_ADMIN_EMAIL", "longtran.pix@gmail.com")
    TEABLE_ADMIN_PASSWORD: str = os.getenv("TEABLE_ADMIN_PASSWORD", "long2710jkl")

    # Server Configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

settings = Settings()
