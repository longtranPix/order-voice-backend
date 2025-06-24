# API Routes Documentation for Frontend Developers

## Overview

This document describes all available API endpoints in the Order Voice Backend, with special focus on update operations. Use this as a reference when implementing frontend API calls.

## Base URL

All endpoints are relative to the base URL: `https://your-api-domain.com`

## Authentication Endpoints

### Sign In
- **URL**: `/auth/signin`
- **Method**: `POST`
- **Description**: Authenticate a user with username and password
- **Request Body**:
  ```json
  {
    "username": "user123",
    "password": "password123"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "message": "Authentication successful",
    "record": [
      {
        "id": "rec123456",
        "fields": {
          "username": "user123",
          "business_name": "My Business",
          "table_order_id": "tbl123456",
          "table_order_detail_id": "tbl789012",
          "table_invoice_info_id": "tbl345678"
        }
      }
    ]
  }
  ```

### Sign Up
- **URL**: `/auth/signup`
- **Method**: `POST`
- **Description**: Register a new user account with tables creation
- **Request Body**:
  ```json
  {
    "username": "newuser",
    "password": "password123",
    "business_name": "My New Business"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Account, workspace, database and tables created successfully",
    "account_id": "rec123456",
    "table_order_id": "tbl123456",
    "table_order_detail_id": "tbl789012",
    "table_invoice_info_id": "tbl345678"
  }
  ```

## Transcription Endpoints

### Transcribe Audio
- **URL**: `/transcription/transcribe`
- **Method**: `POST`
- **Description**: Transcribe audio file and extract order information
- **Request Body**: `multipart/form-data` with audio file
- **Response**:
  ```json
  {
    "language": "vi",
    "transcription": "Tôi muốn đặt một cà phê sữa đá giá 35 nghìn và một bánh mì thịt giá 25 nghìn",
    "extracted": [
      {"ten_hang_hoa": "cà phê sữa đá", "so_luong": 1, "don_gia": 35000},
      {"ten_hang_hoa": "bánh mì thịt", "so_luong": 1, "don_gia": 25000}
    ]
  }
  ```

## Order Endpoints

### Create Order
- **URL**: `/orders/create`
- **Method**: `POST`
- **Description**: Create a new order with details
- **Request Body**:
  ```json
  {
    "customer_name": "Nguyễn Văn A",
    "invoice_state": true,
    "order_details": [
      {"product_name": "cà phê sữa đá", "quantity": 2, "unit_price": 35000, "vat": 10},
      {"product_name": "bánh mì thịt", "quantity": 1, "unit_price": 25000, "vat": 10}
    ],
    "order_table_id": "tbl123456789",
    "detail_table_id": "tbl987654321"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "order": {
      "id": "rec123456",
      "fields": {
        "customer_name": "Nguyễn Văn A",
        "invoice_state": true,
        "total_temp": 95000,
        "total_vat": 9500,
        "total_after_vat": 104500
      }
    },
    "total_temp": 95000,
    "total_vat": 9500,
    "total_after_vat": 104500,
    "invoice_state": true
  }
  ```

### Update Order (Proposed)
- **URL**: `/orders/update/{record_id}`
- **Method**: `PATCH`
- **Description**: Update an existing order
- **URL Parameters**: `record_id` - The ID of the order to update
- **Request Body**:
  ```json
  {
    "order_table_id": "tbl123456789",
    "fields": {
      "customer_name": "Nguyễn Văn B",
      "invoice_state": false
    }
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Order updated successfully",
    "order_id": "rec123456"
  }
  ```

## Invoice Endpoints

### Generate Invoice
- **URL**: `/invoices/generate`
- **Method**: `POST`
- **Description**: Generate invoice using Viettel API
- **Request Body**:
  ```json
  {
    "username": "user123",
    "order_table_id": "tbl123456789",
    "record_order_id": "rec123456789",
    "invoice_payload": {
      "generalInvoiceInfo": {
        "templateCode": "01GTKT0/001",
        "invoiceType": "01GTKT",
        "currencyCode": "VND"
      },
      "buyerInfo": {
        "buyerName": "Nguyễn Văn A",
        "buyerLegalName": "Công ty TNHH A"
      },
      "payments": [
        {
          "paymentMethodName": "TM/CK"
        }
      ],
      "items": [
        {
          "lineNumber": 1,
          "itemName": "Cà phê sữa đá",
          "unitPrice": 35000,
          "quantity": 2,
          "itemTotalAmountWithoutVat": 70000,
          "vatPercentage": 10
        }
      ]
    }
  }
  ```
- **Response**:
  ```json
  {
    "detail": "Invoice generated successfully",
    "invoice_no": "0000123",
    "file_name": "invoice_0000123.pdf"
  }
  ```

## Update Operations

Currently, the API doesn't have dedicated update endpoints for most resources. Updates are handled through the following internal mechanism:

### Internal Update Record Function
The backend uses a `update_record` function in the `TeableService` class to update records in Teable:

```python
async def update_record(
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
        return response.status_code == 200
    except Exception as e:
        return False
```

### Proposed Update Endpoints for Frontend

To make the API more RESTful and easier to use from the frontend, we recommend implementing the following update endpoints:

#### 1. Update User Profile
- **URL**: `/auth/users/{user_id}`
- **Method**: `PATCH`
- **Description**: Update user profile information
- **Request Body**:
  ```json
  {
    "business_name": "Updated Business Name",
    "password": "new_password"  // Optional
  }
  ```

#### 2. Update Order
- **URL**: `/orders/{order_id}`
- **Method**: `PATCH`
- **Description**: Update an existing order
- **Request Body**:
  ```json
  {
    "customer_name": "Updated Customer Name",
    "invoice_state": true
  }
  ```

#### 3. Update Order Details
- **URL**: `/orders/{order_id}/details/{detail_id}`
- **Method**: `PATCH`
- **Description**: Update a specific order detail item
- **Request Body**:
  ```json
  {
    "product_name": "Updated Product Name",
    "quantity": 3,
    "unit_price": 40000,
    "vat": 8
  }
  ```

#### 4. Update Invoice Information
- **URL**: `/invoices/{invoice_id}`
- **Method**: `PATCH`
- **Description**: Update invoice information
- **Request Body**:
  ```json
  {
    "template_code": "01GTKT0/002",
    "invoice_series": ["AA/20E"]
  }
  ```

## Implementation Notes for Frontend Developers

1. **Authentication**: All endpoints except `/auth/signin` and `/auth/signup` require authentication.

2. **Error Handling**: All endpoints return appropriate HTTP status codes:
   - `200/201`: Success
   - `400`: Bad request (invalid input)
   - `401`: Unauthorized
   - `404`: Resource not found
   - `409`: Conflict (e.g., username already exists)
   - `500`: Server error

3. **CORS**: The API has CORS enabled for frontend access from the following origins:
   - `http://localhost:3000`
   - `http://localhost:8080`
   - Additional origins can be configured via environment variables

4. **Request Format**: All requests should include:
   - `Content-Type: application/json` header (except for file uploads)
   - Authentication token in the `Authorization` header (when required)

5. **Response Format**: All responses follow a consistent format:
   - Success responses include a `status` field with value `"success"`
   - Error responses include a `detail` field with error message

## Example: Updating an Order from Frontend

```javascript
// Example using fetch API
async function updateOrder(orderId, tableId, updateData) {
  try {
    const response = await fetch(`/orders/update/${orderId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        order_table_id: tableId,
        fields: updateData
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to update order');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error updating order:', error);
    throw error;
  }
}

// Usage
updateOrder('rec123456', 'tbl123456789', {
  customer_name: 'Updated Customer Name',
  invoice_state: false
})
  .then(data => console.log('Order updated:', data))
  .catch(error => console.error('Update failed:', error));
```