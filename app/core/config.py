import os
from typing import List

class Settings:
    """Application settings and configuration."""

    # API Configuration - will be loaded from environment variables
    TEABLE_BASE_URL: str = "https://app.teable.io/api"
    TEABLE_TOKEN: str = ""  # Will be loaded from .env
    TEABLE_TABLE_ID: str = "tblv9Ou1thzbETynKn1"

    # Invoice API Configuration
    CREATE_INVOICE_URL: str = "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceWS/createInvoice"
    GET_PDF_URL: str = "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceUtilsWS/getInvoiceRepresentationFile"

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Whisper Model Configuration
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_DEVICE: str = "cpu"

    # Application Configuration
    APP_NAME: str = "Order Voice Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    def __init__(self):
        # Load from environment variables with fallbacks
        self.TEABLE_BASE_URL = os.getenv("TEABLE_BASE_URL", self.TEABLE_BASE_URL)
        self.TEABLE_TOKEN = os.getenv("TEABLE_TOKEN", self.TEABLE_TOKEN)
        self.TEABLE_TABLE_ID = os.getenv("TEABLE_TABLE_ID", self.TEABLE_TABLE_ID)
        self.CREATE_INVOICE_URL = os.getenv("CREATE_INVOICE_URL", self.CREATE_INVOICE_URL)
        self.GET_PDF_URL = os.getenv("GET_PDF_URL", self.GET_PDF_URL)
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"

        # Validate required environment variables
        if not self.TEABLE_TOKEN:
            raise ValueError("TEABLE_TOKEN environment variable is required")

        # Parse CORS origins from environment
        cors_origins = os.getenv("ALLOWED_ORIGINS", "*")
        if cors_origins == "*":
            self.CORS_ORIGINS = ["*"]
        else:
            self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",")]

settings = Settings()
