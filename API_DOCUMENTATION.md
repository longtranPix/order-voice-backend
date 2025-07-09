# 📚 API Documentation

## 🔐 Authentication APIs

### 1. User Signup
**Endpoint:** `POST /auth/signup`

**Description:** Register a new business account and create complete workspace with all necessary tables.

**Headers:**
```
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "username": "0316316874",
  "password": "cubable2025"
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Tài khoản, không gian, cơ sở dữ liệu và tất cả các bảng đã được tạo thành công",
  "account_id": "recUser123",
  "business_name": "CÔNG TY CỔ PHẦN CUBABLE",
  "taxcode": "0316316874",
  "workspace": {
    "space_id": "spcCubable123",
    "base_id": "baseCubable456",
    "access_token": "teable_accABC123XYZ789..."
  },
  "tables": {
    "order_table_id": "tblOrders001",
    "order_detail_table_id": "tblOrderDetails001",
    "customer_table_id": "tblCustomers001",
    "product_table_id": "tblProducts001",
    "import_slip_id": "tblImportSlips001",
    "import_slip_details_id": "tblImportDetails001",
    "delivery_note_id": "tblDeliveryNotes001",
    "delivery_note_details_id": "tblDeliveryDetails001"
  }
}
```

### 2. User Signin
**Endpoint:** `POST /auth/signin`

**Description:** Authenticate user and return access token for API operations.

**Headers:**
```
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "username": "0316316874",
  "password": "cubable2025"
}
```

**Response:**
```json
{
  "status": "success",
  "accessToken": "teable_accABC123XYZ789DEF456GHI012JKL345",
  "detail": "Xác thực thành công",
  "record": [
    {
      "id": "recUser123",
      "fields": {
        "username": "0316316874",
        "business_name": "CÔNG TY CỔ PHẦN CUBABLE",
        "last_login": "2025-01-02T10:30:00"
      }
    }
  ]
}
```

## 📦 Inventory Management APIs

### 3. Create Import Slip
**Endpoint:** `POST /create-import-slip`

**Description:** Create import slip to stock inventory with products from suppliers.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "supplier_id": "recSupplier001",
  "import_type": "Nhập mua",
  "import_slip_details": [
    {
      "product_id": "recProduct001",
      "unit_conversions_id": "recUnitConv001",
      "quantity": 50,
      "unit_price": 14000000,
      "vat": 10
    },
    {
      "product_id": "recProduct002",
      "unit_conversions_id": "recUnitConv005",
      "quantity": 100,
      "unit_price": 450000,
      "vat": 10
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Phiếu nhập đã được tạo thành công",
  "import_slip_id": "recImportSlip001",
  "import_slip_code": "PN-02012025-001",
  "import_slip_details_ids": ["recImportDetail001", "recImportDetail002"],
  "total_items": 2,
  "total_amount": 819500000
}
```

### 4. Create Delivery Note
**Endpoint:** `POST /create-delivery-note`

**Description:** Create delivery note for order fulfillment and inventory tracking.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "order_id": "recOrder001",
  "customer_id": "recCustomer001",
  "delivery_type": "Xuất bán",
  "delivery_note_details": [
    {
      "product_id": "recProduct001",
      "quantity": 2,
      "unit_price": 15000000,
      "vat": 10
    },
    {
      "product_id": "recProduct002",
      "quantity": 2,
      "unit_price": 500000,
      "vat": 10
    }
  ],
  "notes": "Giao hàng cho đơn hàng DH-02012025-001"
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Phiếu xuất đã được tạo thành công",
  "delivery_note_id": "recDeliveryNote001",
  "delivery_note_code": "PX-02012025-001",
  "delivery_note_details_ids": ["recDeliveryDetail001", "recDeliveryDetail002"],
  "order_id": "recOrder001",
  "customer_id": "recCustomer001",
  "total_items": 2,
  "total_amount": 34100000
}
```

## 🛒 Order Management APIs

### 5. Create Order with Automatic Delivery Note
**Endpoint:** `POST /orders/create-order`

**Description:** Process customer orders with automatic delivery note creation. Uses customer_id and product_id instead of names, includes unit_conversions_id for proper unit tracking.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "customer_id": "recCustomer001",
  "order_details": [
    {
      "product_id": "recProduct001",
      "unit_conversions_id": "recUnitConv001",
      "unit_price": 15000000,
      "quantity": 2,
      "vat": 10
    },
    {
      "product_id": "recProduct002",
      "unit_conversions_id": "recUnitConv002",
      "unit_price": 500000,
      "quantity": 2,
      "vat": 10
    }
  ],
  "delivery_type": "Xuất bán"
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Đơn hàng và phiếu xuất đã được tạo thành công",
  "order_id": "recOrder001",
  "order_code": "DH-02012025-001",
  "delivery_note_id": "recDeliveryNote001",
  "delivery_note_code": "PX-02012025-001",
  "customer_id": "recCustomer001",
  "total_items": 2,
  "total_temp": 31000000,
  "total_vat": 3100000,
  "total_after_vat": 34100000
}
```

## 🧾 Invoice Management APIs

### 6. Generate Invoice
**Endpoint:** `POST /invoices/generate-invoice`

**Description:** Generate official invoices for tax compliance and business records.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "username": "0316316874",
  "buyerName": "Nguyễn Văn An",
  "buyerTaxCode": "",
  "buyerAddressLine": "123 Đường Lê Lợi, Quận 1, TP.HCM",
  "buyerEmail": "nguyenvanan@email.com",
  "buyerPhone": "0901234567",
  "items": [
    {
      "itemName": "Laptop Dell Inspiron 15",
      "unitPrice": 15000000,
      "quantity": 2,
      "itemTotalAmountWithoutTax": 30000000,
      "taxPercentage": 10,
      "taxAmount": 3000000,
      "itemTotalAmountWithTax": 33000000
    },
    {
      "itemName": "Chuột không dây Logitech",
      "unitPrice": 500000,
      "quantity": 2,
      "itemTotalAmountWithoutTax": 1000000,
      "taxPercentage": 10,
      "taxAmount": 100000,
      "itemTotalAmountWithTax": 1100000
    }
  ],
  "totalAmountWithoutTax": 31000000,
  "totalTaxAmount": 3100000,
  "totalAmountWithTax": 34100000,
  "paymentMethod": "Chuyển khoản"
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Hóa đơn đã được tạo thành công",
  "invoice_code": "HD-02012025-001",
  "pdf_url": "https://invoice-service.com/invoices/HD-02012025-001.pdf",
  "total_amount": 34100000
}
```

## 👥 Customer Management APIs

### 7. Create Customer
**Endpoint:** `POST /customers/create-customer`

**Description:** Create new customer record in the customer table.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "phone_number": "0901234567",
  "fullname": "Nguyễn Văn An",
  "address": "123 Đường Lê Lợi, Quận 1, TP.HCM",
  "email": "nguyenvanan@email.com"
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Khách hàng đã được tạo thành công",
  "customer_id": "recCustomer001",
  "customer_data": {
    "customer_id": "recCustomer001",
    "phone_number": "0901234567",
    "fullname": "Nguyễn Văn An",
    "address": "123 Đường Lê Lợi, Quận 1, TP.HCM",
    "email": "nguyenvanan@email.com"
  }
}
```

### 8. Find Customer by Name
**Endpoint:** `GET /customers/find-by-name`

**Description:** Search for customers by name with partial matching.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```
GET /customers/find-by-name?name=Nguyễn Văn&limit=10

Query Parameters:
- name: "Nguyễn Văn" (partial customer name)
- limit: 10 (optional, default: 10)
```

**Response:**
```json
{
  "status": "success",
  "detail": "Tìm thấy 2 khách hàng",
  "customers": [
    {
      "customer_id": "recCustomer001",
      "phone_number": "0901234567",
      "fullname": "Nguyễn Văn An",
      "address": "123 Đường Lê Lợi, Quận 1, TP.HCM",
      "email": "nguyenvanan@email.com"
    },
    {
      "customer_id": "recCustomer002",
      "phone_number": "0907654321",
      "fullname": "Nguyễn Văn Bình",
      "address": "456 Đường Nguyễn Huệ, Quận 3, TP.HCM",
      "email": "nguyenvanbinh@email.com"
    }
  ],
  "total_found": 2
}
```

## ⚖️ Unit Conversion Management APIs

### 9. Create Unit Conversion
**Endpoint:** `POST /unit-conversions/create-unit-conversion`

**Description:** Create new unit conversion record for product measurements.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "name_unit": "Thùng",
  "conversion_factor": 12,
  "unit_default": "Hộp",
  "price": 150000
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Đơn vị tính đã được tạo thành công",
  "unit_conversion_id": "recUnitConv001",
  "unit_conversion_data": {
    "unit_conversion_id": "recUnitConv001",
    "name_unit": "Thùng",
    "conversion_factor": 12,
    "unit_default": "Hộp",
    "price": 150000
  }
}
```

### 10. Get Unit Conversions
**Endpoint:** `GET /unit-conversions/list`

**Description:** Get all available unit conversions for the user.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```
GET /unit-conversions/list
```

**Response:**
```json
{
  "status": "success",
  "detail": "Tìm thấy 6 đơn vị tính",
  "unit_conversions": [
    {
      "unit_conversion_id": "recUnitConv001",
      "name_unit": "Chiếc",
      "conversion_factor": 1,
      "unit_default": "Chiếc",
      "price": 0
    },
    {
      "unit_conversion_id": "recUnitConv002",
      "name_unit": "Hộp",
      "conversion_factor": 1,
      "unit_default": "Hộp",
      "price": 0
    },
    {
      "unit_conversion_id": "recUnitConv003",
      "name_unit": "Thùng",
      "conversion_factor": 12,
      "unit_default": "Hộp",
      "price": 150000
    },
    {
      "unit_conversion_id": "recUnitConv004",
      "name_unit": "Kg",
      "conversion_factor": 1,
      "unit_default": "Kg",
      "price": 0
    },
    {
      "unit_conversion_id": "recUnitConv005",
      "name_unit": "Gram",
      "conversion_factor": 0.001,
      "unit_default": "Kg",
      "price": 0
    },
    {
      "unit_conversion_id": "recUnitConv006",
      "name_unit": "Tấn",
      "conversion_factor": 1000,
      "unit_default": "Kg",
      "price": 0
    }
  ],
  "total_found": 6
}
```

## 📦 Product Management APIs

### 11. Create Product
**Endpoint:** `POST /products/create-product`

**Description:** Create new product record in the product catalog.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "product_name": "Laptop Dell Inspiron 15",
  "unit_price": 15000000,
  "unit_conversions": ["recUnitConv001", "recUnitConv002"],
  "vat_rate": 10,
  "category": "Laptop",
  "brand": "Dell",
  "inventory": 50
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Sản phẩm đã được tạo thành công",
  "product_id": "recProduct001",
  "product_data": {
    "product_id": "recProduct001",
    "product_name": "Laptop Dell Inspiron 15",
    "unit_price": 15000000,
    "unit_conversions": ["recUnitConv001", "recUnitConv002"],
    "vat_rate": 10,
    "category": "Laptop",
    "brand": "Dell",
    "inventory": 50
  }
}
```

### 10. Create Product with Inline Units
**Endpoint:** `POST /products/create-product-with-units`

**Description:** Create product with inline unit conversion creation in a single atomic operation.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "product_name": "Nước ngọt Coca Cola",
  "unit_conversions": [
    {
      "name_unit": "Chai",
      "conversion_factor": 1,
      "unit_default": "Chai",
      "price": 15000,
      "vat": 10
    },
    {
      "name_unit": "Lốc",
      "conversion_factor": 24,
      "unit_default": "Chai",
      "price": 350000,
      "vat": 8
    },
    {
      "name_unit": "Thùng",
      "conversion_factor": 288,
      "unit_default": "Chai",
      "price": 4200000,
      "vat": 5
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Sản phẩm và 3 đơn vị tính đã được tạo thành công",
  "product_id": "recProduct001",
  "product_data": {
    "product_id": "recProduct001",
    "product_name": "Nước ngọt Coca Cola",
    "unit_conversions": ["recUnitConv007", "recUnitConv008", "recUnitConv009"]
  },
  "created_unit_conversions": [
    {
      "unit_conversion_id": "recUnitConv007",
      "name_unit": "Chai",
      "conversion_factor": 1,
      "unit_default": "Chai",
      "price": 15000,
      "vat": 10
    },
    {
      "unit_conversion_id": "recUnitConv008",
      "name_unit": "Lốc",
      "conversion_factor": 24,
      "unit_default": "Chai",
      "price": 350000,
      "vat": 8
    },
    {
      "unit_conversion_id": "recUnitConv009",
      "name_unit": "Thùng",
      "conversion_factor": 288,
      "unit_default": "Chai",
      "price": 4200000,
      "vat": 5
    }
  ]
}
```

### 11. Find Product by Name
**Endpoint:** `GET /products/find-by-name`

**Description:** Search for products by name with partial matching.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```
GET /products/find-by-name?name=Laptop Dell&category=Laptop&limit=10

Query Parameters:
- name: "Laptop Dell" (partial product name)
- category: "Laptop" (optional filter by category)
- limit: 10 (optional, default: 10)
```

**Response:**
```json
{
  "status": "success",
  "detail": "Tìm thấy 3 sản phẩm",
  "products": [
    {
      "product_id": "recProduct001",
      "product_name": "Laptop Dell Inspiron 15",
      "unit_price": 15000000,
      "unit_conversions": ["recUnitConv001"],
      "vat_rate": 10,
      "category": "Laptop",
      "brand": "Dell",
      "inventory": 50
    },
    {
      "product_id": "recProduct002",
      "product_name": "Laptop Dell XPS 13",
      "unit_price": 25000000,
      "unit_conversions": ["recUnitConv001"],
      "vat_rate": 10,
      "category": "Laptop",
      "brand": "Dell",
      "inventory": 30
    },
    {
      "product_id": "recProduct003",
      "product_name": "Laptop Dell Latitude 14",
      "unit_price": 18000000,
      "unit_conversions": ["recUnitConv001"],
      "vat_rate": 10,
      "category": "Laptop",
      "brand": "Dell",
      "inventory": 25
    }
  ],
  "total_found": 3
}
```

## 🎤 Voice Processing APIs

### 12. Audio Transcription
**Endpoint:** `POST /transcribe/`

**Description:** Process voice orders and extract product information from Vietnamese speech.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: multipart/form-data
Accept: application/json
```

**Request:**
```
Multipart form data with audio file:
- file: [audio file] (Vietnamese speech: "Tôi muốn đặt hai laptop Dell Inspiron và một chuột Logitech")
```

**Response:**
```json
{
  "language": "vi",
  "transcription": "Tôi muốn đặt hai laptop Dell Inspiron và một chuột Logitech",
  "extracted": {
    "products": [
      {
        "name": "laptop Dell Inspiron",
        "quantity": 2
      },
      {
        "name": "chuột Logitech",
        "quantity": 1
      }
    ],
    "customer_info": "Không có thông tin khách hàng trong audio"
  }
}
```

---

## 📊 Teable API Integration

### 8. Create Customer
**Endpoint:** `POST /customers/create-customer`

**Description:** Create new customer record in the customer table.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "phone_number": "0901234567",
  "fullname": "Nguyễn Văn An",
  "address": "123 Đường Lê Lợi, Quận 1, TP.HCM",
  "email": "nguyenvanan@email.com"
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Khách hàng đã được tạo thành công",
  "customer_id": "recCustomer001",
  "customer_data": {
    "phone_number": "0901234567",
    "fullname": "Nguyễn Văn An",
    "address": "123 Đường Lê Lợi, Quận 1, TP.HCM",
    "email": "nguyenvanan@email.com"
  }
}
```

### 9. Create Product
**Endpoint:** `POST /products/create-product`

**Description:** Create new product record in the product catalog.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```json
{
  "product_name": "Laptop Dell Inspiron 15",
  "unit_price": 15000000,
  "unit": "Chiếc",
  "vat_rate": 10,
  "category": "Laptop",
  "brand": "Dell",
  "inventory": 50
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Sản phẩm đã được tạo thành công",
  "product_id": "recProduct001",
  "product_data": {
    "product_name": "Laptop Dell Inspiron 15",
    "unit_price": 15000000,
    "unit": "Chiếc",
    "vat_rate": 10,
    "category": "Laptop",
    "brand": "Dell",
    "inventory": 50
  }
}
```

### 10. Find Customer by Name
**Endpoint:** `GET /customers/find-by-name`

**Description:** Search for customers by name with partial matching.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```
GET /customers/find-by-name?name=Nguyễn Văn

Query Parameters:
- name: "Nguyễn Văn" (partial customer name)
- limit: 10 (optional, default: 10)
```

**Response:**
```json
{
  "status": "success",
  "detail": "Tìm thấy 2 khách hàng",
  "customers": [
    {
      "customer_id": "recCustomer001",
      "phone_number": "0901234567",
      "fullname": "Nguyễn Văn An",
      "address": "123 Đường Lê Lợi, Quận 1, TP.HCM",
      "email": "nguyenvanan@email.com"
    },
    {
      "customer_id": "recCustomer002",
      "phone_number": "0907654321",
      "fullname": "Nguyễn Văn Bình",
      "address": "456 Đường Nguyễn Huệ, Quận 3, TP.HCM",
      "email": "nguyenvanbinh@email.com"
    }
  ],
  "total_found": 2
}
```

### 11. Find Product by Name
**Endpoint:** `GET /products/find-by-name`

**Description:** Search for products by name with partial matching.

**Headers:**
```
Authorization: Bearer teable_accABC123XYZ789DEF456GHI012JKL345
Content-Type: application/json
Accept: application/json
```

**Request:**
```
GET /products/find-by-name?name=Laptop Dell

Query Parameters:
- name: "Laptop Dell" (partial product name)
- category: "Laptop" (optional filter by category)
- limit: 10 (optional, default: 10)
```

**Response:**
```json
{
  "status": "success",
  "detail": "Tìm thấy 3 sản phẩm",
  "products": [
    {
      "product_id": "recProduct001",
      "product_name": "Laptop Dell Inspiron 15",
      "unit_price": 15000000,
      "unit": "Chiếc",
      "vat_rate": 10,
      "category": "Laptop",
      "brand": "Dell",
      "inventory": 50
    },
    {
      "product_id": "recProduct002",
      "product_name": "Laptop Dell XPS 13",
      "unit_price": 25000000,
      "unit": "Chiếc",
      "vat_rate": 10,
      "category": "Laptop",
      "brand": "Dell",
      "inventory": 30
    },
    {
      "product_id": "recProduct003",
      "product_name": "Laptop Dell Latitude 14",
      "unit_price": 18000000,
      "unit": "Chiếc",
      "vat_rate": 10,
      "category": "Laptop",
      "brand": "Dell",
      "inventory": 25
    }
  ],
  "total_found": 3
}
```

### 13. Get User Table Information
**Endpoint:** `GET {TEABLE_BASE_URL}/table/{TEABLE_TABLE_ID}/record`

**Description:** Internal API for retrieving user's table IDs and configuration.

**Headers:**
```
Authorization: Bearer teable_accAFr0SCGDTUqXQTQb_+7LBL2ZrQJH/EN6utEyKq057Q0SEfVVFqrn0iDAu9aw=
Content-Type: application/json
Accept: application/json
```

**Request:**
```
GET https://app.teable.vn/api/table/tblj52nsIFcIWDAW4fr/record?fieldKeyType=dbFieldName&viewId=viwxhGxe8OL1tprQ2Qz&filter={"conjunction":"and","filterSet":[{"fieldId":"username","operator":"is","value":"0316316874"}]}

Parameters:
- fieldKeyType: "dbFieldName"
- viewId: "viwxhGxe8OL1tprQ2Qz"
- filter: {"conjunction":"and","filterSet":[{"fieldId":"username","operator":"is","value":"0316316874"}]}
```

**Response:**
```json
{
  "records": [
    {
      "fields": {
        "username": "0316316874",
        "table_product_id": "tblwzOLEFxI33KMHHwQ",
        "access_token": "teable_acc2iuGS0YAlRkl745i_mvpKXmanvgZfDvaoO5zbtj2PjlzHKjLq9mJe8Zm73YA=",
        "table_order_id": "tbllBc4GFKntEl6hxMX",
        "table_order_detail_id": "tblNtEhz9O2sdrrGTwf",
        "table_customer_id": "tblG6BfsMld7WGfdhoQ",
        "table_import_slip_details_id": "tblJgYdYcu7ptyc5dzE",
        "table_delivery_note_details_id": "tbl9mO6JDsV7uvGSBnI",
        "table_delivery_note_id": "tblx4wVhAmopAVXI9YS",
        "table_import_slip_id": "tblyshSa4VbAXMQrTTC"
      },
      "name": "0316316874",
      "id": "recTEsSEocN4vkmUtQv",
      "autoNumber": 15,
      "createdTime": "2025-07-01T08:13:58.034Z",
      "lastModifiedTime": "2025-07-01T09:17:39.229Z"
    }
  ]
}
```

**Retrieved Information:**
- `table_product_id`: Product catalog table
- `table_order_id`: Main orders table
- `table_order_detail_id`: Order details table
- `table_customer_id`: Customer management table
- `table_import_slip_id`: Import slips table
- `table_import_slip_details_id`: Import slip details table
- `table_delivery_note_id`: Delivery notes table
- `table_delivery_note_details_id`: Delivery note details table
- `access_token`: User's workspace access token

**Usage in APIs:**
This information is automatically retrieved by import slip and delivery note APIs to:
1. Identify the correct tables for the authenticated user
2. Use the user's workspace access token for operations
3. Ensure data isolation between different businesses
4. Enable proper table linking and relationships

## 🔐 Security & Authorization

All APIs (except auth endpoints) require:
- **Bearer Token Authentication**: User's space access token
- **User Isolation**: Each user can only access their own workspace tables
- **Token Validation**: Real-time verification against token list table
- **ViewId Filtering**: Specific views for controlled data access

## 🔧 Technical Implementation Details

### Teable API Integration Architecture

**Base Configuration:**
```python
TEABLE_BASE_URL = "https://app.teable.vn/api"
TEABLE_TABLE_ID = "tblj52nsIFcIWDAW4fr"  # Main user table
TEABLE_USER_VIEW_ID = "viwWOH429ek2bW3eU06"  # User info view
TEABLE_TOKEN_LIST_TABLE_ID = "tblR7dckuSizsZlhW47"  # Token registry
```

**User Table Info Retrieval Function:**
```python
async def get_user_table_info(username: str) -> dict:
    """Get user table information using viewId"""
    headers = {
        "Authorization": settings.TEABLE_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    params = {
        "fieldKeyType": "dbFieldName",
        "viewId": "viwxhGxe8OL1tprQ2Qz",  # Specific view for table info
        "filter": json.dumps({
            "conjunction": "and",
            "filterSet": [
                {"fieldId": "username", "operator": "is", "value": username}
            ]
        })
    }

    url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
    result = handle_teable_api_call("GET", url, params=params, headers=headers)

    return result["data"]["records"][0]["fields"]
```

**Token Management:**
- **Token Registry Table**: `tblR7dckuSizsZlhW47`
- **Fields**: `username` (taxcode), `token` (space access token)
- **Purpose**: Centralized token management and user authentication

**Data Flow:**
1. User authenticates → Get space token from registry
2. API call → Retrieve user table info using viewId
3. Extract table IDs → Use for specific operations
4. Execute operations → Use user's workspace token

### Field Mappings

**Import Slip Details Table:**
- `product_link`: Links to product table
- `unit_conversions`: Links to unit conversions table
- `quantity`: Import quantity
- `unit_price`: Import price per unit
- `vat`: VAT percentage
- `number_detail`: Auto-generated detail number

**Delivery Note Details Table:**
- `product_link`: Links to product table
- `quantity`: Delivery quantity
- `number_detail`: Auto-generated detail number

**Product Table:**
- `inventory`: Current stock level (updated by import/export)

## 📋 Error Handling

All APIs return consistent error responses:
```json
{
  "detail": "Error message in Vietnamese",
  "status_code": 400
}
```

Common error codes:
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (invalid token)
- `404`: Not Found (user/resource not found)
- `500`: Internal Server Error

**Specific Error Cases:**
- **Missing Table IDs**: "Thiếu thông tin bảng cần thiết"
- **Invalid Token**: "Invalid token or token not found"
- **User Not Found**: "Không tìm thấy thông tin người dùng"
- **API Call Failed**: "Không thể tạo phiếu nhập/xuất"
