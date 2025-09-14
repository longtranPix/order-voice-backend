## API request/response scripts

Set a base URL for your environment:

### 1) Sign in

Request:

```bash
curl -X POST "$BASE_URL/auth/signin" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "0316316874",
    "password": "your_password"
  }'
```

Response (example):

```json
{
  "status": "success",
  "detail": "Xác thực thành công",
  "record": [
    {
      "fields": {
        "username": "29112001",
        "business_name": "Shop Long",
        "password": "NOLA_tPUM+Zvk3ZudMWz1cHsosxslaHzOLmvCKkB3tjBXwEM=_PWD",
        "table_order_id": "tblvR7DQasShwvIlHex",
        "table_order_detail_id": "tbleKiLAwG0i1uNvrAM",
        "invoice_token": "MjkxMTIwMDE6MTIzMTIz",
        "last_login": "2025-09-10T17:29:00.000Z",
        "access_token": "teable_accZfgNsAlwmShHZjmc_JW+R6WlEWm5lsMUbByfHkzshrGSTaZDfAxetKtlzu/Y="
      },
      "name": "29112001",
      "id": "recIMcGTTawR4kMogN1",
      "autoNumber": 13,
      "createdTime": "2025-09-09T18:28:35.554Z",
      "lastModifiedTime": "2025-09-10T17:31:01.711Z",
      "createdBy": "usr6cQql0CGD5qqSuPX",
      "lastModifiedBy": "usr6cQql0CGD5qqSuPX"
    }
  ]
}
```

Save the token for later calls:

```bash
TOKEN=eyJhbGciOi...
```

### 2) Get current user (/auth/me)

Request:

```bash
curl -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

Response (example):

```json
{
  "status": "success",
  "message": "Lấy thông tin người dùng thành công",
  "data": {
    "username": "0316316874",
    "business_name": "Công ty Cổ phần CUBABLE",
    "current_plan_name": "Nâng cao",
    "last_login": "2025-07-08T10:28:23.478+07:00",
    "time_expired": "2025-07-31T00:00:00+07:00",
    "tax_code": "0316316874",
    "bank_name": "Vietcombank",
    "bank_number": "1234567890",
    "account_name": "Công ty Cổ phần CUBABLE"
  }
}
```

### 3) Update profile (/user/update-profile)

Request (all fields optional):

```bash
curl -X PATCH "$BASE_URL/user/update-profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Công ty Cổ phần CUBABLE Updated",
    "tax_code": "0316316874",
    "bank_name": "Vietcombank",
    "bank_number": "1234567890",
    "account_name": "Công ty Cổ phần CUBABLE"
  }'
```

Response (example):

```json
{
  "status": "success",
  "message": "Cập nhật thông tin thành công",
  "data": {
    "username": "0316316874",
    "business_name": "Công ty Cổ phần CUBABLE Updated",
    "current_plan_name": "Nâng cao",
    "last_login": "2025-07-08T10:35:12.123+07:00",
    "time_expired": "2025-07-31T00:00:00+07:00",
    "tax_code": "0316316874",
    "bank_name": "Vietcombank",
    "bank_number": "1234567890",
    "account_name": "Công ty Cổ phần CUBABLE"
  }
}
```

### 4) Create order (/orders/create-order)

Request body only requires business fields; table IDs are resolved from token:

```bash
curl -X POST "$BASE_URL/orders/create-order" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_code": "DHddmmyy-xxxx",
    "customer_name": "Nguyễn Văn A",
    "payment_method": "Chuyển khoản | Tiền mặt",
    "order_details": [
      { "product_name": "Sản phẩm 1", "unit_price": 100000, "quantity": 2, "vat_rate": 10 },
      { "product_name": "Sản phẩm 2", "unit_price": 50000,  "quantity": 1, "vat_rate": 8 }
    ]
  }'
```

Response (example):

```json
{
  "status": "success",
  "order": {
    "records": [
      { "id": "recOrder123", "fields": { "order_code": "DH001", "customer_name": "Nguyễn Văn A", "payment_method": "Chuyển khoản", "detail_orders": ["recDet1","recDet2"] } }
    ]
  },
  "total_temp": 250000.0,
  "total_vat": 28000.0,
  "total_after_vat": 278000.0
}
```

### 5) Get plan status (/plan-status/get-status-plan)

Request:

```bash
curl -X GET "$BASE_URL/plan-status/get-status-plan" \
  -H "Authorization: Bearer $TOKEN"
```

Response (example):

```json
{
  "status": "success",
  "message": "Lấy thông tin plan status thành công",
  "data": {
    "fields": {
      "started_time": "2025-07-15T08:44:38.952Z",
      "cycle": 12,
      "time_expired": "2026-07-15T08:44:38.952Z",
      "status": "Đang hoạt động",
      "credit_value": 4000,
      "name_plan": "Cơ bản"
    },
    "name": "1",
    "id": "recgBj8j7A9lz2DNJdz",
    "autoNumber": 1,
    "createdTime": "2025-07-15T08:44:38.952Z",
    "lastModifiedTime": "2025-07-17T09:05:06.690Z",
    "createdBy": "usr6cQql0CGD5qqSuPX",
    "lastModifiedBy": "usr6cQql0CGD5qqSuPX"
  }
}
```

### 6) Get order report (/reports/order-report)

Request:

```bash
curl -X POST "$BASE_URL/reports/order-report" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-01-31T23:59:59Z"
  }'
```

Response (example):

```json
{
  "status": "success",
  "message": "Báo cáo đơn hàng được tạo thành công",
  "data": {
    "date_range": {
      "start_date": "2025-01-01T00:00:00Z",
      "end_date": "2025-01-31T23:59:59Z"
    },
    "summary": {
      "total_orders": 25,
      "total_temp": 5000000,
      "total_vat": 500000,
      "total_with_tax": 5500000
    },
    "daily_breakdown": {
      "2025-01-01": 200000,
      "2025-01-02": 300000,
      "2025-01-15": 500000
    }
  }
}
```

Notes:

- Always pass `Authorization: Bearer $TOKEN` obtained from signin.
- Order detail fields supported: `product_name` (string), `unit_price` (number), `quantity` (integer), `vat_rate` (percent number).
- Computed totals in Teable (rollups) are not sent in payload; they are returned in the response for convenience.
- Plan status is automatically retrieved from the authenticated user's current plan.
- Report uses `created_time` field to filter orders within the specified date range.

