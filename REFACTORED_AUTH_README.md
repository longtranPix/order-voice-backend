# 🔐 Refactored Authentication System

## 📋 Overview

This document describes the comprehensive refactoring of the authentication system based on the SIGNUP_API_IMPLEMENTATION_GUIDE.md. The system now includes:

- **Secure Password Encoding**: HMAC-SHA256 with custom salt
- **JWT Authentication**: Token-based API protection
- **Template-based Database Creation**: Automatic workspace setup
- **Comprehensive Error Handling**: Proper HTTP status codes and logging
- **Protected API Endpoints**: Authentication middleware for all sensitive operations

## 🏗️ Architecture

### File Structure
```
app/
├── constants/
│   └── auth_data.py          # Table mappings and constants
├── core/
│   └── config.py             # Environment configuration
├── routes/
│   ├── auth.py               # Authentication endpoints
│   ├── orders.py             # Protected order endpoints
│   └── invoices.py           # Protected invoice endpoints
├── schemas/
│   └── auth.py               # Request/response models
├── services/
│   └── auth_service.py       # Core authentication logic
└── utils/
    ├── auth_utils.py         # Password encoding & Teable helpers
    └── jwt_auth.py           # JWT authentication middleware
```

## 🔐 Authentication Flow

### 1. User Signup Process
```
1. Validate taxcode via VietQR API
2. Check for existing user
3. Encode password with HMAC-SHA256
4. Create user account in Teable
5. Create workspace and space
6. Generate access token
7. Create database from template
8. Extract table IDs
9. Update user record with all IDs
```

### 2. User Signin Process
```
1. Find user by username (taxcode)
2. Verify encoded password
3. Update last_login timestamp
4. Return access token
```

### 3. API Protection
```
1. Client includes JWT token in Authorization header
2. Middleware validates token
3. Extracts user information
4. Provides user context to protected endpoints
```

## 🛡️ Security Features

### Password Encoding
- **Algorithm**: HMAC-SHA256
- **Salt**: Username + timestamp + length
- **Secret Key**: Multi-source derivation
- **Format**: `CUBABLE_{encoded}_PWD`

### JWT Authentication
- **Algorithm**: HS256
- **Expiry**: 30 minutes (configurable)
- **Claims**: Username, Teable token, token type
- **Refresh**: Token refresh endpoint available

### API Protection
- **Bearer Token**: Required for protected endpoints
- **User Context**: Automatic user identification
- **Table Isolation**: Users only access their own data

## 📡 API Endpoints

### Public Endpoints
```
POST /auth/signup     # User registration
POST /auth/signin     # User authentication
```

### Protected Endpoints
```
GET  /auth/me         # Current user info
POST /auth/refresh    # Refresh token
POST /orders/create-order  # Create order
GET  /orders/orders   # Get user orders
```

## 🔧 Configuration

### Environment Variables
```bash
# Copy env_template.txt to .env and configure:
TEABLE_BASE_URL=https://app.teable.vn/api
TEABLE_TOKEN=Bearer your_token_here
TEABLE_TABLE_ID=your_table_id
TEABLE_ADMIN_EMAIL=admin@example.com
TEABLE_ADMIN_PASSWORD=admin_password
JWT_SECRET_KEY=your-secret-key
```

### Dependencies
```bash
pip install -r requirements.txt
```

## 🚀 Usage Examples

### 1. User Signup
```bash
curl -X POST "http://localhost:8000/auth/signup" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "0316316874",
       "password": "securepassword123"
     }'
```

**Response:**
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
    "table_product_id": "tblProducts001"
  }
}
```

### 2. User Signin
```bash
curl -X POST "http://localhost:8000/auth/signin" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "0316316874",
       "password": "securepassword123"
     }'
```

**Response:**
```json
{
  "status": "success",
  "accessToken": "teable_accABC123XYZ789...",
  "detail": "Xác thực thành công",
  "record": [...]
}
```

### 3. Protected API Call
```bash
curl -X POST "http://localhost:8000/orders/create-order" \
     -H "Authorization: Bearer teable_accABC123XYZ789..." \
     -H "Content-Type: application/json" \
     -d '{
       "customer_name": "John Doe",
       "items": [...]
     }'
```

## 🔒 Security Best Practices

### 1. Password Security
- Passwords are never stored in plain text
- HMAC-SHA256 with unique salt per user
- Salt includes username and password length

### 2. Token Management
- JWT tokens have short expiry (30 minutes)
- Teable access tokens for long-term access
- Token refresh mechanism available

### 3. API Security
- All sensitive endpoints require authentication
- User context automatically extracted from tokens
- Table access isolated by user workspace

### 4. Error Handling
- No sensitive information in error messages
- Proper HTTP status codes
- Comprehensive logging for debugging

## 🧪 Testing

### 1. Test Signup Flow
```bash
# Test with valid taxcode
curl -X POST "http://localhost:8000/auth/signup" \
     -H "Content-Type: application/json" \
     -d '{"username": "0316316874", "password": "test123"}'

# Test with invalid taxcode
curl -X POST "http://localhost:8000/auth/signup" \
     -H "Content-Type: application/json" \
     -d '{"username": "invalid", "password": "test123"}'
```

### 2. Test Authentication
```bash
# Test signin with correct credentials
curl -X POST "http://localhost:8000/auth/signin" \
     -H "Content-Type: application/json" \
     -d '{"username": "0316316874", "password": "test123"}'

# Test signin with wrong password
curl -X POST "http://localhost:8000/auth/signin" \
     -H "Content-Type: application/json" \
     -d '{"username": "0316316874", "password": "wrong"}'
```

### 3. Test Protected Endpoints
```bash
# Test without token (should fail)
curl -X GET "http://localhost:8000/auth/me"

# Test with valid token
curl -X GET "http://localhost:8000/auth/me" \
     -H "Authorization: Bearer your_token_here"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Template ID Not Found
- **Error**: "Không thể tạo cơ sở dữ liệu từ template"
- **Solution**: Update `TEMPLATE_ID` in `app/constants/auth_data.py`

#### 2. Admin Login Fails
- **Error**: "Admin login failed"
- **Solution**: Verify `TEABLE_ADMIN_EMAIL` and `TEABLE_ADMIN_PASSWORD`

#### 3. JWT Token Invalid
- **Error**: "Could not validate credentials"
- **Solution**: Check `JWT_SECRET_KEY` and token expiry

#### 4. Table Mapping Errors
- **Error**: Missing table IDs in response
- **Solution**: Update `TABLE_NAME_MAPPING` in `app/constants/auth_data.py`

### Debug Mode
Enable detailed logging by setting:
```bash
LOG_LEVEL=DEBUG
```

## 🔄 Migration from Old System

### 1. Update Configuration
- Copy new environment variables from `env_template.txt`
- Update Teable configuration
- Set JWT secret key

### 2. Database Changes
- New users will automatically get template-based databases
- Existing users can continue using current setup
- No data migration required

### 3. API Changes
- All endpoints now return structured responses
- Authentication required for sensitive operations
- Error handling improved

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **JWT Documentation**: https://pyjwt.readthedocs.io/
- **Teable API Documentation**: https://docs.teable.io/
- **Original Implementation Guide**: `SIGNUP_API_IMPLEMENTATION_GUIDE.md`

## 🎯 Next Steps

1. **Implement Password Reset**: Forgot password functionality
2. **Add User Roles**: Admin, manager, user permissions
3. **Audit Logging**: Track all authentication events
4. **Rate Limiting**: Prevent brute force attacks
5. **Two-Factor Authentication**: Additional security layer
6. **API Versioning**: Support multiple API versions

---

This refactored system provides a robust, secure, and scalable authentication foundation for the Order Voice Backend application.
