import os
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Teable API Configuration
    TEABLE_BASE_URL: str = os.getenv("TEABLE_BASE_URL", "https://app.teable.vn/api")
    TEABLE_TOKEN: str = os.getenv("TEABLE_TOKEN", "Bearer teable_accT1cTLbgDxAw73HQa_xnRuWiEDLat6qqpUDsL4QEzwnKwnkU9ErG7zgJKJswg=")
    TEABLE_TABLE_ID: str = os.getenv("TEABLE_TABLE_ID", "tblnXmPFvtyGdWeBYYl")
    TEABLE_USER_VIEW_ID: str = os.getenv("TEABLE_USER_VIEW_ID", "viwWe3GY2fGizREKab6")
    TEABLE_TOKEN_LIST_TABLE_ID: str = os.getenv("TEABLE_TOKEN_LIST_TABLE_ID", "your_token_table_id")
    TEABLE_TEMPLATE_ID: str = os.getenv("TEABLE_TEMPLATE_ID", "tplW9q8pznJabsAL3Eh")
    TEABLE_USER_TOKEN_VIEW_ID: str = os.getenv("TEABLE_USER_TOKEN_VIEW_ID", "viwWe3GY2fGizREKab6")
    TEABLE_PLAN_STATUS_TABLE_ID: str = os.getenv("TEABLE_PLAN_STATUS_TABLE_ID", "tblL2pLkyLQgPzmCVHU")
    
    # Admin credentials for token generation
    TEABLE_ADMIN_EMAIL: str = os.getenv("TEABLE_ADMIN_EMAIL", "longtran.pix@gmail.com")
    TEABLE_ADMIN_PASSWORD: str = os.getenv("TEABLE_ADMIN_PASSWORD", "long2710jkl")
    
    # External APIs
    VIETQR_BASE_URL: str = os.getenv("VIETQR_BASE_URL", "https://api.vietqr.io/v2/business")
    
    # Invoice API Configuration
    CREATE_INVOICE_URL: str = os.getenv("CREATE_INVOICE_URL", "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceWS/createInvoice")
    GET_PDF_URL: str = os.getenv("GET_PDF_URL", "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceUtilsWS/getInvoiceRepresentationFile")
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Password encoding constants
    PASSWORD_PREFIX: str = os.getenv("PASSWORD_PREFIX", "NOLA_")
    PASSWORD_SUFFIX: str = os.getenv("PASSWORD_SUFFIX", "_PWD")
    SECRET_KEY_PREFIX: str = os.getenv("SECRET_KEY_PREFIX", "CUBABLE_SECRET_")
    SALT_PREFIX: str = os.getenv("SALT_PREFIX", "_CUBABLE_2025_")

    # Server Configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS Configuration
    # Comma-separated values, e.g. "http://localhost:3000,https://example.com" or "*"
    CORS_ALLOWED_ORIGINS_RAW: str = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    CORS_ALLOWED_METHODS_RAW: str = os.getenv("CORS_ALLOWED_METHODS", "*")
    CORS_ALLOWED_HEADERS_RAW: str = os.getenv("CORS_ALLOWED_HEADERS", "*")

    @property
    def CORS_ALLOWED_ORIGINS(self) -> List[str]:
        raw = self.CORS_ALLOWED_ORIGINS_RAW.strip()
        if raw == "*" or raw == "":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def CORS_ALLOWED_METHODS(self) -> List[str]:
        raw = self.CORS_ALLOWED_METHODS_RAW.strip()
        if raw == "*" or raw == "":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def CORS_ALLOWED_HEADERS(self) -> List[str]:
        raw = self.CORS_ALLOWED_HEADERS_RAW.strip()
        if raw == "*" or raw == "":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]

settings = Settings()
