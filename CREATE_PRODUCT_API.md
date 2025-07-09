# Create Product API Documentation

## Overview

The Create Product API allows you to create products with flexible unit conversions and individual VAT rates. This API has been updated to move pricing and VAT configuration from the product level to the unit conversion level, providing more granular control over pricing and tax structures.

## Key Features

- ✅ **Simplified Product Structure**: Products now focus on core identity (name + unit conversions)
- ✅ **Unit-Level VAT**: Individual VAT rates for each unit conversion
- ✅ **Flexible Pricing**: Different prices for different unit sizes
- ✅ **Atomic Operations**: Create product with all unit conversions in a single transaction
- ✅ **Rollback Support**: Automatic cleanup if any part of the creation fails

## API Endpoints

### 1. Create Product with Inline Unit Conversions

**Endpoint:** `POST /products/create-product-with-units`

**Description:** Create a product with multiple unit conversions in a single atomic operation. Each unit conversion can have its own price and VAT rate.

#### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: application/json
```

#### Request Schema

```json
{
  "product_name": "string",
  "unit_conversions": [
    {
      "name_unit": "string",
      "conversion_factor": "number",
      "unit_default": "string", 
      "price": "number",
      "vat": "number (default: 10.0)"
    }
  ]
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_name` | string | Yes | Name of the product |
| `unit_conversions` | array | Yes | Array of unit conversion objects |
| `unit_conversions[].name_unit` | string | Yes | Name of the unit (e.g., "Chai", "Lốc", "Thùng") |
| `unit_conversions[].conversion_factor` | number | Yes | Conversion factor to default unit |
| `unit_conversions[].unit_default` | string | Yes | Default unit for conversion |
| `unit_conversions[].price` | number | Yes | Price for this unit conversion |
| `unit_conversions[].vat` | number | No | VAT rate for this unit (default: 10.0%) |

#### Example Request

```json
{
  "product_name": "Nước ngọt Coca Cola 330ml",
  "unit_conversions": [
    {
      "name_unit": "Chai",
      "conversion_factor": 1,
      "unit_default": "Chai",
      "price": 15000,
      "vat": 10.0
    },
    {
      "name_unit": "Lốc 24 chai",
      "conversion_factor": 24,
      "unit_default": "Chai",
      "price": 350000,
      "vat": 8.0
    },
    {
      "name_unit": "Thùng 12 lốc",
      "conversion_factor": 288,
      "unit_default": "Chai",
      "price": 4200000,
      "vat": 5.0
    }
  ]
}
```

#### Response Schema

```json
{
  "status": "string",
  "detail": "string",
  "product_id": "string",
  "product_data": {
    "product_id": "string",
    "product_name": "string",
    "unit_conversions": ["string"]
  },
  "created_unit_conversions": [
    {
      "unit_conversion_id": "string",
      "name_unit": "string",
      "conversion_factor": "number",
      "unit_default": "string",
      "price": "number",
      "vat": "number"
    }
  ]
}
```

#### Example Response

```json
{
  "status": "success",
  "detail": "Sản phẩm và 3 đơn vị tính đã được tạo thành công",
  "product_id": "recProduct001",
  "product_data": {
    "product_id": "recProduct001",
    "product_name": "Nước ngọt Coca Cola 330ml",
    "unit_conversions": ["recUnitConv001", "recUnitConv002", "recUnitConv003"]
  },
  "created_unit_conversions": [
    {
      "unit_conversion_id": "recUnitConv001",
      "name_unit": "Chai",
      "conversion_factor": 1,
      "unit_default": "Chai",
      "price": 15000,
      "vat": 10.0
    },
    {
      "unit_conversion_id": "recUnitConv002",
      "name_unit": "Lốc 24 chai",
      "conversion_factor": 24,
      "unit_default": "Chai",
      "price": 350000,
      "vat": 8.0
    },
    {
      "unit_conversion_id": "recUnitConv003",
      "name_unit": "Thùng 12 lốc",
      "conversion_factor": 288,
      "unit_default": "Chai",
      "price": 4200000,
      "vat": 5.0
    }
  ]
}
```

### 2. Create Basic Product

**Endpoint:** `POST /products/create-product`

**Description:** Create a basic product with existing unit conversion IDs.

#### Request Schema

```json
{
  "product_name": "string",
  "unit_conversions": ["string"]
}
```

#### Example Request

```json
{
  "product_name": "Nước ngọt Pepsi 330ml",
  "unit_conversions": ["recUnitConv004", "recUnitConv005"]
}
```

## Business Use Cases

### Flexible VAT Structure

Different unit sizes can have different VAT rates based on business rules:

- **Retail Units** (Chai): 10% VAT - Standard retail rate
- **Small Wholesale** (Lốc): 8% VAT - Reduced rate for small bulk
- **Large Wholesale** (Thùng): 5% VAT - Lowest rate for large bulk

### Pricing Strategies

Unit conversions enable flexible pricing strategies:

```
Coca Cola 330ml:
├── Chai (1x): 15,000 VND per unit = 15,000 VND/chai
├── Lốc (24x): 350,000 VND per unit = 14,583 VND/chai (3% discount)
└── Thùng (288x): 4,200,000 VND per unit = 14,583 VND/chai (3% discount)
```

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Không thể tạo đơn vị tính 'Lốc': Invalid conversion factor"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Token không hợp lệ hoặc đã hết hạn"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Lỗi không mong muốn khi tạo sản phẩm với đơn vị tính"
}
```

### Rollback Mechanism

If any unit conversion fails to create, the API automatically:
1. Deletes all previously created unit conversions
2. Returns an error response
3. Ensures data consistency

## Integration Examples

### JavaScript/Node.js

```javascript
const createProduct = async (productData) => {
  try {
    const response = await fetch('/products/create-product-with-units', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(productData)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      console.log('Product created:', result.product_id);
      console.log('Unit conversions:', result.created_unit_conversions);
    } else {
      console.error('Error:', result.detail);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};
```

### Python

```python
import requests

def create_product(product_data, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        '/products/create-product-with-units',
        json=product_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Product created: {result['product_id']}")
        return result
    else:
        print(f"Error: {response.json()['detail']}")
        return None
```

## Best Practices

1. **VAT Configuration**: Set appropriate VAT rates based on your business requirements and local tax regulations
2. **Unit Naming**: Use clear, descriptive unit names that users can easily understand
3. **Conversion Factors**: Ensure conversion factors are accurate for inventory tracking
4. **Price Consistency**: Verify that bulk pricing makes business sense
5. **Error Handling**: Always handle potential errors and provide user feedback
6. **Testing**: Test with various unit combinations before production use

## Migration Notes

### From Previous Version

If migrating from the previous API version:

**Old Structure:**
```json
{
  "product_name": "Product",
  "unit_price": 15000,
  "vat_rate": 10,
  "unit_conversions": [...]
}
```

**New Structure:**
```json
{
  "product_name": "Product",
  "unit_conversions": [
    {
      "name_unit": "Unit",
      "price": 15000,
      "vat": 10,
      ...
    }
  ]
}
```

### Key Changes

- ❌ Removed `unit_price` from product level
- ❌ Removed `vat_rate` from product level  
- ✅ Added `price` to each unit conversion
- ✅ Added `vat` to each unit conversion
- ✅ More flexible pricing and tax structure
