# 🚀 Signup API Implementation Guide

## 📋 Overview

This guide provides comprehensive instructions for building a complete signup API system that creates user accounts, workspaces, and database structures automatically. The system is designed for Vietnamese businesses using tax codes as usernames.

## 🏗️ Architecture Overview

The signup API follows a multi-step process:
1. **Validation**: Check if user already exists
2. **User Creation**: Create user account with encoded password
3. **Workspace Setup**: Create Teable space and base from template
4. **Database Structure**: Extract and map all table IDs
5. **Token Management**: Generate access tokens and store in registry
6. **Response**: Return complete workspace information

## 📁 File Structure

```
app/
├── services/
│   └── auth_service.py          # Main signup logic
├── routes/
│   └── auth.py                  # API endpoints
├── schemas/
│   └── auth.py                  # Request/response models
├── constants/
│   └── auth_data.py             # Table configurations
├── core/
│   └── config.py                # Environment settings
└── utils/
    └── auth_utils.py            # Helper functions
```

## 🔧 Core Components

### 1. Request Schema (`app/schemas/auth.py`)

```python
from pydantic import BaseModel

class SignUp(BaseModel):
    username: str  # Tax code (e.g., "0316316874")
    password: str  # User password
```

### 2. Configuration (`app/core/config.py`)

```python
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    # Teable API Configuration
    TEABLE_BASE_URL: str = os.getenv("TEABLE_BASE_URL", "https://app.teable.vn/api")
    TEABLE_TOKEN: str = os.getenv("TEABLE_TOKEN", "Bearer your_token_here")
    TEABLE_TABLE_ID: str = os.getenv("TEABLE_TABLE_ID", "your_table_id")
    TEABLE_USER_VIEW_ID: str = os.getenv("TEABLE_USER_VIEW_ID", "your_view_id")
    TEABLE_TOKEN_LIST_TABLE_ID: str = os.getenv("TEABLE_TOKEN_LIST_TABLE_ID", "your_token_table_id")
    
    # Admin credentials for token generation
    TEABLE_ADMIN_EMAIL: str = os.getenv("TEABLE_ADMIN_EMAIL", "admin@example.com")
    TEABLE_ADMIN_PASSWORD: str = os.getenv("TEABLE_ADMIN_PASSWORD", "admin_password")

settings = Settings()
```

### 3. API Endpoint (`app/routes/auth.py`)

```python
from fastapi import APIRouter
from app.schemas.auth import SignUp
from app.services.auth_service import signup_service

router = APIRouter()

@router.post("/signup")
async def signup(account: SignUp):
    """User signup endpoint"""
    return await signup_service(account)
```

## 🔐 Password Encoding System

### Private Encoding Rules

The system uses a custom password encoding mechanism with the following rules:

```python
def encode_password(password: str, username: str) -> str:
    """
    Encode password using private rules for secure storage
    
    Private encoding rules:
    1. Combine password with username as salt
    2. Apply HMAC-SHA256 with secret key
    3. Add timestamp-based rotation
    4. Base64 encode final result
    """
    try:
        # Private rule 1: Create salt from username with rotation
        salt = f"{username}_CUBABLE_2025_{len(password)}"

        # Private rule 2: Create secret key from multiple sources
        secret_key = f"CUBABLE_SECRET_{username[:3]}_{len(username)}_ORDER_VOICE_2025"

        # Private rule 3: Combine password with salt and apply transformations
        combined = f"{password}:{salt}:{len(password + username)}"

        # Private rule 4: Apply HMAC-SHA256 with secret key
        encoded_bytes = hmac.new(
            secret_key.encode('utf-8'),
            combined.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Private rule 5: Add additional layer with base64 and custom suffix
        final_encoded = base64.b64encode(encoded_bytes).decode('utf-8')

        # Private rule 6: Add custom prefix and suffix for identification
        result = f"CUBABLE_{final_encoded}_PWD"

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi mã hóa mật khẩu"
        )
```

## 🏢 Workspace Creation Process

### Step 1: User Validation

```python
# Check if user already exists
existing_user_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
headers = {
    "Authorization": settings.TEABLE_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

check_params = {
    "fieldKeyType": "dbFieldName",
    "filter": json.dumps({
        "conjunction": "and",
        "filterSet": [{"fieldId": "username", "operator": "is", "value": taxcode}]
    })
}

existing_result = handle_teable_api_call("GET", existing_user_url, params=check_params, headers=headers)
if existing_result["success"] and len(existing_result.get("data", {}).get("records")) > 0:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tài khoản đã tồn tại"
    )
```

### Step 2: Create User Account

```python
# Encode password using private rules
encoded_password = encode_password(account.password, taxcode)

# Create invoice token (separate from password encoding)
encoded_str = base64.b64encode(f"{taxcode}:{account.password}".encode()).decode()

user_record_payload = {
    "typecast": True,
    "records": [{
        "fields": {
            "username": taxcode,
            "password": encoded_password,  # Store encoded password
            "business_name": business_name,
            "invoice_token": encoded_str
        }
    }],
    "fieldKeyType": "dbFieldName"
}

user_result = handle_teable_api_call("POST", existing_user_url, data=json.dumps(user_record_payload), headers=headers)
```

### Step 3: Create Teable Space

```python
# Create space
space_name = f"{business_name}_workspace"
space_response = requests.post(
    f"{settings.TEABLE_BASE_URL}/space", 
    data=json.dumps({"name": space_name}), 
    headers=headers
)
if space_response.status_code != 201:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail=f"Không thể tạo không gian làm việc: {space_response.text}"
    )
space_id = space_response.json()["id"]
```

### Step 4: Generate Access Token

```python
# Generate access token immediately after space creation
access_token = await generate_space_access_token(space_id, space_name, headers)

# Create record in token registry table
if access_token:
    await create_token_registry_record(taxcode, access_token, headers)
```

### Step 5: Create Base from Template

```python
# Create base from template (NEW APPROACH)
template_payload = {
    "spaceId": space_id,
    "templateId": "tpl2qOKQjJtcJI3C7R6",  # Your template ID
    "withRecords": False
}

base_response = requests.post(
    f"{settings.TEABLE_BASE_URL}/base/create-from-template",
    data=json.dumps(template_payload),
    headers=space_headers  # Use space access token
)

if base_response.status_code != 201:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Không thể tạo cơ sở dữ liệu từ template: {base_response.text}"
    )

base_data = base_response.json()
base_id = base_data["id"]
```

### Step 6: Extract Table Information

```python
# Get all table information from the created base
tables_response = requests.get(
    f"{settings.TEABLE_BASE_URL}/base/{base_id}/table",
    headers=space_headers
)

tables_data = tables_response.json()

# Map table names to IDs based on template structure
table_mapping = {}
for table in tables_data:
    table_name = table["name"]
    table_id = table["id"]
    table_mapping[table_name] = table_id

# Extract table IDs based on expected table names from template
table_name_mapping = {
    "Khách Hàng": "table_customer_id",
    "Đơn Vị Tính Chuyển Đổi": "table_unit_conversions_id",
    "Thương Hiệu": "table_brand_id",
    "Sản Phẩm": "table_product_id",
    "Chi Tiết Đơn Hàng": "table_order_detail_id",
    "Đơn Hàng": "table_order_id",
    "Thông Tin Hóa Đơn": "table_invoice_info_id",
    "Chi Tiết Phiếu Nhập": "table_import_slip_details_id",
    "Chi Tiết Phiếu Xuất": "table_delivery_note_details_id",
    "Phiếu Xuất": "table_delivery_note_id",
    "Nhà Cung Cấp": "table_supplier_id",
    "Phiếu Nhập": "table_import_slip_id",
    "Danh Mục": "table_catalog_id",
    "Ngành Hàng": "table_product_line_id",
    "Thuộc Tính": "table_attribute_id",
    "Tên Thuộc Tính": "table_attribute_type_id"
}

# Extract table IDs
extracted_table_ids = {}
for template_name, field_name in table_name_mapping.items():
    if template_name in table_mapping:
        extracted_table_ids[field_name] = table_mapping[template_name]
```

### Step 7: Update User Record

```python
# Update user record with all table IDs and access token
update_fields = {
    "invoice_token": encoded_str,
    "upload_file_id": upload_file_id,
    "access_token": access_token
}

# Add all extracted table IDs to update fields
update_fields.update(extracted_table_ids)

update_success = update_user_table_id(settings.TEABLE_TABLE_ID, record_id, update_fields)
```

## 📊 Database Table Structure

The system creates a comprehensive database structure with the following tables:

### Core Tables
- **Khách Hàng** (Customers): Customer information
- **Sản Phẩm** (Products): Product catalog
- **Đơn Vị Tính Chuyển Đổi** (Unit Conversions): Unit conversion rates
- **Thương Hiệu** (Brands): Product brands

### Order Management
- **Đơn Hàng** (Orders): Main order records
- **Chi Tiết Đơn Hàng** (Order Details): Order line items

### Inventory Management
- **Phiếu Nhập** (Import Slips): Stock import records
- **Chi Tiết Phiếu Nhập** (Import Slip Details): Import line items
- **Phiếu Xuất** (Delivery Notes): Stock export records
- **Chi Tiết Phiếu Xuất** (Delivery Note Details): Export line items

### Supporting Tables
- **Nhà Cung Cấp** (Suppliers): Supplier information
- **Thông Tin Hóa Đơn** (Invoice Info): Invoice configuration
- **Danh Mục** (Catalog): Product categories
- **Ngành Hàng** (Product Line): Product lines
- **Thuộc Tính** (Attributes): Product attributes
- **Tên Thuộc Tính** (Attribute Types): Attribute type definitions

## 🔑 Token Management System

### Access Token Generation

```python
async def generate_space_access_token(space_id: str, space_name: str, headers: dict) -> str:
    """Generate access token for the created space"""
    try:
        # Login as admin to get session
        login_data = {
            "email": settings.TEABLE_ADMIN_EMAIL,
            "password": settings.TEABLE_ADMIN_PASSWORD
        }
        
        login_response = requests.post(
            f"{settings.TEABLE_BASE_URL}/auth/login",
            data=json.dumps(login_data),
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            logger.error(f"Admin login failed: {login_response.text}")
            return ""
        
        session_token = login_response.json().get("accessToken", "")
        if not session_token:
            logger.error("No session token received from admin login")
            return ""
        
        # Generate access token for the space
        token_headers = {
            "Authorization": f"Bearer {session_token}",
            "Content-Type": "application/json"
        }
        
        token_data = {
            "spaceId": space_id,
            "name": f"Access Token for {space_name}"
        }
        
        token_response = requests.post(
            f"{settings.TEABLE_BASE_URL}/space/{space_id}/access-token",
            data=json.dumps(token_data),
            headers=token_headers
        )
        
        if token_response.status_code == 201:
            return token_response.json().get("accessToken", "")
        else:
            logger.error(f"Token generation failed: {token_response.text}")
            return ""
            
    except Exception as e:
        logger.error(f"Error generating access token: {str(e)}")
        return ""
```

### Token Registry

```python
async def create_token_registry_record(username: str, access_token: str, headers: dict):
    """Create record in token registry table"""
    try:
        registry_payload = {
            "typecast": True,
            "records": [{
                "fields": {
                    "username": username,
                    "access_token": access_token,
                    "created_at": datetime.now().isoformat()
                }
            }],
            "fieldKeyType": "dbFieldName"
        }
        
        registry_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TOKEN_LIST_TABLE_ID}/record"
        result = handle_teable_api_call("POST", registry_url, data=json.dumps(registry_payload), headers=headers)
        
        if result["success"]:
            logger.info(f"Token registry record created for user: {username}")
        else:
            logger.error(f"Failed to create token registry record: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error creating token registry record: {str(e)}")
```

## 📝 API Response Format

### Success Response

```json
{
  "status": "success",
  "detail": "Tài khoản, không gian, cơ sở dữ liệu và tất cả các bảng đã được tạo thành công",
  "account_id": "recUser123",
  "business_name": "Shop_0316316874",
  "taxcode": "0316316874",
  "workspace": {
    "space_id": "spcCubable123",
    "base_id": "baseCubable456",
    "access_token": "teable_accABC123XYZ789..."
  },
  "tables": {
    "table_customer_id": "tblCustomers001",
    "table_unit_conversions_id": "tblUnitConversions001",
    "table_brand_id": "tblBrands001",
    "table_product_id": "tblProducts001",
    "table_order_detail_id": "tblOrderDetails001",
    "table_order_id": "tblOrders001",
    "table_invoice_info_id": "tblInvoiceInfo001",
    "table_import_slip_details_id": "tblImportDetails001",
    "table_delivery_note_details_id": "tblDeliveryDetails001",
    "table_delivery_note_id": "tblDeliveryNotes001",
    "table_supplier_id": "tblSuppliers001",
    "table_import_slip_id": "tblImportSlips001",
    "table_catalog_id": "tblCatalog001",
    "table_product_line_id": "tblProductLine001",
    "table_attribute_id": "tblAttributes001",
    "table_attribute_type_id": "tblAttributeTypes001"
  },
  "upload_file_id": "fldUploadFile001"
}
```

### Error Response

```json
{
  "detail": "Tài khoản đã tồn tại"
}
```

## 🛠️ Helper Functions

### Teable API Handler

```python
def handle_teable_api_call(method: str, url: str, **kwargs) -> dict:
    """Handle Teable API calls with error handling"""
    try:
        response = requests.request(method, url, **kwargs)
        
        if response.status_code in [200, 201]:
            return {
                "success": True,
                "data": response.json(),
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 500
        }
```

### User Table Update

```python
def update_user_table_id(table_id: str, record_id: str, update_fields: dict) -> bool:
    """Update user table record with new fields"""
    try:
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        update_payload = {
            "typecast": True,
            "records": [{
                "id": record_id,
                "fields": update_fields
            }],
            "fieldKeyType": "dbFieldName"
        }
        
        update_url = f"{settings.TEABLE_BASE_URL}/table/{table_id}/record"
        result = handle_teable_api_call("PATCH", update_url, data=json.dumps(update_payload), headers=headers)
        
        return result["success"]
    except Exception as e:
        logger.error(f"Error updating user table: {str(e)}")
        return False
```

## 🔧 Environment Variables

Create a `.env` file with the following variables:

```env
# Teable API Configuration
TEABLE_BASE_URL=https://app.teable.vn/api
TEABLE_TOKEN=Bearer your_teable_token_here
TEABLE_TABLE_ID=your_user_table_id
TEABLE_USER_VIEW_ID=your_user_view_id
TEABLE_TOKEN_LIST_TABLE_ID=your_token_registry_table_id

# Admin credentials for token generation
TEABLE_ADMIN_EMAIL=admin@example.com
TEABLE_ADMIN_PASSWORD=admin_password

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

## 🚀 Implementation Steps

### 1. Setup Dependencies

```bash
pip install fastapi uvicorn requests python-dotenv pydantic
```

### 2. Create Project Structure

```
mkdir -p app/{services,routes,schemas,constants,core,utils}
touch app/__init__.py
touch app/services/__init__.py
touch app/routes/__init__.py
touch app/schemas/__init__.py
touch app/constants/__init__.py
touch app/core/__init__.py
touch app/utils/__init__.py
```

### 3. Implement Core Files

1. **Configuration**: `app/core/config.py`
2. **Schemas**: `app/schemas/auth.py`
3. **Constants**: `app/constants/auth_data.py`
4. **Utils**: `app/utils/auth_utils.py`
5. **Service**: `app/services/auth_service.py`
6. **Routes**: `app/routes/auth.py`

### 4. Main Application

```python
# main.py
from fastapi import FastAPI
from app.routes.auth import router as auth_router

app = FastAPI(title="Signup API", version="1.0.0")

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 5. Run the Application

```bash
python main.py
```

## 🧪 Testing

### Test Request

```bash
curl -X POST "http://localhost:8000/auth/signup" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "0316316874",
       "password": "testpassword123"
     }'
```

### Expected Response

```json
{
  "status": "success",
  "detail": "Tài khoản, không gian, cơ sở dữ liệu và tất cả các bảng đã được tạo thành công",
  "account_id": "recUser123",
  "business_name": "Shop_0316316874",
  "taxcode": "0316316874",
  "workspace": {
    "space_id": "spcCubable123",
    "base_id": "baseCubable456",
    "access_token": "teable_accABC123XYZ789..."
  },
  "tables": {
    "table_customer_id": "tblCustomers001",
    "table_product_id": "tblProducts001",
    // ... other table IDs
  }
}
```

## 🔒 Security Considerations

1. **Password Encoding**: Uses custom HMAC-SHA256 encoding with salt
2. **Token Management**: Secure access token generation and storage
3. **Input Validation**: Pydantic models for request validation
4. **Error Handling**: Comprehensive error handling and logging
5. **Environment Variables**: Sensitive data stored in environment variables

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Teable API Documentation**: https://docs.teable.io/
- **Pydantic Documentation**: https://pydantic-docs.helpmanual.io/

## 🐛 Common Issues and Solutions

### 1. Template ID Not Found
- **Issue**: Template ID `tpl2qOKQjJtcJI3C7R6` doesn't exist
- **Solution**: Replace with your actual template ID from Teable

### 2. Token Generation Fails
- **Issue**: Access token generation fails
- **Solution**: Verify admin credentials and API permissions

### 3. Table Mapping Errors
- **Issue**: Table names don't match template
- **Solution**: Update `table_name_mapping` dictionary with correct names

### 4. Environment Variables Missing
- **Issue**: Configuration errors
- **Solution**: Ensure all required environment variables are set

## 🎯 Next Steps

After implementing the signup API:

1. **Implement Signin API**: User authentication
2. **Add Password Change**: Password update functionality
3. **User Profile Management**: Profile CRUD operations
4. **Business Logic APIs**: Orders, products, customers
5. **Invoice Integration**: E-invoice generation
6. **Testing Suite**: Comprehensive test coverage

This guide provides everything needed to build a complete signup API system. The modular design allows for easy extension and maintenance.
