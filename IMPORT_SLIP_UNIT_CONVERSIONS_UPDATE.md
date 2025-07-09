# Import Slip Unit Conversions Update

## Overview

Updated the Create Import Slip API to include `unit_conversions_id` as a required field in import slip details. This ensures proper linking to the unit conversions table for accurate inventory tracking and unit standardization.

## Changes Made

### 1. 📋 **Schema Update**

**File:** `app/schemas/import_slips.py`

**Before:**
```python
class ImportSlipDetailItem(BaseModel):
    """Schema for import slip detail item"""
    product_id: str  # ID of product from product table
    quantity: float
    unit_price: float
    vat: float = 10.0  # Default VAT 10%
```

**After:**
```python
class ImportSlipDetailItem(BaseModel):
    """Schema for import slip detail item"""
    product_id: str  # ID of product from product table
    unit_conversions_id: str  # ID of unit conversion from unit conversions table
    quantity: float
    unit_price: float
    vat: float = 10.0  # Default VAT 10%
```

### 2. 🔧 **Service Logic Update**

**File:** `app/services/import_slip_service.py`

**Before:**
```python
detail_record = {
    "fields": {
        "product_link": [detail.product_id],  # Link to product table
        "quantity": detail.quantity,
        "unit_price": detail.unit_price,
        "vat": detail.vat,
        "temp_total": temp_total,
        "final_total": final_total
    }
}

# Add unit conversions link if provided
if hasattr(detail, 'unit_conversions_id') and detail.unit_conversions_id:
    detail_record["fields"]["unit_conversions"] = [detail.unit_conversions_id]
```

**After:**
```python
detail_record = {
    "fields": {
        "product_link": [detail.product_id],  # Link to product table
        "unit_conversions": [detail.unit_conversions_id],  # Link to unit conversions table
        "quantity": detail.quantity,
        "unit_price": detail.unit_price,
        "vat": detail.vat,
        "temp_total": temp_total,
        "final_total": final_total
    }
}
```

### 3. 📚 **API Documentation Update**

**File:** `API_DOCUMENTATION.md`

**Before:**
```json
{
  "import_type": "Nhập mua",
  "import_slip_details": [
    {
      "product_id": "recProduct001",
      "quantity": 50,
      "unit_price": 14000000,
      "vat": 10
    }
  ],
  "supplier_name": "Công ty TNHH Phân phối Công nghệ ABC",
  "notes": "Nhập hàng đợt 1 tháng 1/2025"
}
```

**After:**
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
    }
  ]
}
```

### 4. 🧪 **Test Update**

**File:** `test_supplier_integration.py`

**Before:**
```python
"import_slip_details": [
    {
        "product_id": self.created_product_id,
        "quantity": 50,
        "unit_price": 450000,
        "vat": 8.0
    }
]
```

**After:**
```python
"import_slip_details": [
    {
        "product_id": self.created_product_id,
        "unit_conversions_id": self.created_unit_conversion_id,
        "quantity": 50,
        "unit_price": 450000,
        "vat": 8.0
    }
]
```

## API Request Format

### Updated Create Import Slip Request

**Endpoint:** `POST /import-slips/create-import-slip`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "supplier_id": "recSupplier001",
  "import_type": "Nhập mua",
  "import_slip_details": [
    {
      "product_id": "recProduct001",
      "unit_conversions_id": "recUnitConv001",
      "quantity": 50,
      "unit_price": 450000,
      "vat": 8.0
    },
    {
      "product_id": "recProduct002", 
      "unit_conversions_id": "recUnitConv005",
      "quantity": 100,
      "unit_price": 350000,
      "vat": 10.0
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

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `supplier_id` | string | Yes | ID of supplier from supplier table |
| `import_type` | string | No | Type of import (default: "Nhập mua") |
| `import_slip_details` | array | Yes | Array of import detail items |
| `import_slip_details[].product_id` | string | Yes | ID of product from product table |
| `import_slip_details[].unit_conversions_id` | string | Yes | ID of unit conversion from unit conversions table |
| `import_slip_details[].quantity` | number | Yes | Import quantity |
| `import_slip_details[].unit_price` | number | Yes | Import price per unit |
| `import_slip_details[].vat` | number | No | VAT percentage (default: 10.0) |

## Benefits

### ✅ **Proper Unit Tracking**
- Each import slip detail now properly links to unit conversions
- Enables accurate inventory calculations with unit standardization
- Supports multiple unit types for the same product

### ✅ **Data Integrity**
- Required field ensures all import records have unit information
- Prevents incomplete inventory tracking
- Maintains consistency with order and delivery note structures

### ✅ **Business Intelligence**
- Better reporting with unit-specific import data
- Accurate cost analysis per unit type
- Enhanced inventory management capabilities

### ✅ **Consistency**
- Aligns with order details and delivery note details structure
- Uniform unit conversion handling across all transaction types
- Simplified API usage with consistent field requirements

## Database Impact

### Import Slip Details Table Structure
```
Import Slip Details Table:
├── product_link → Product Table (bidirectional)
├── unit_conversions → Unit Conversions Table (bidirectional) ✅ NOW REQUIRED
├── quantity (number)
├── unit_price (number)
├── vat (number)
├── temp_total (number)
└── final_total (number)
```

### Unit Conversion Tracking
- Import quantities properly converted to standard units
- Accurate inventory calculations across different unit types
- Complete audit trail for unit-specific imports

## Migration Notes

### ⚠️ **Breaking Change**
This is a **breaking change** for existing API clients. The `unit_conversions_id` field is now **required** in all import slip detail items.

### Migration Steps for API Clients

1. **Update Request Structure:**
   ```diff
   {
     "supplier_id": "recSupplier001",
     "import_slip_details": [
       {
         "product_id": "recProduct001",
   +     "unit_conversions_id": "recUnitConv001",
         "quantity": 50,
         "unit_price": 450000,
         "vat": 8.0
       }
     ]
   }
   ```

2. **Ensure Unit Conversion Data:**
   - Create unit conversions for all products before importing
   - Use appropriate unit conversion IDs for each import item
   - Verify unit conversion relationships are properly established

3. **Update Error Handling:**
   - Handle validation errors for missing `unit_conversions_id`
   - Verify unit conversion exists before creating import slips

## Testing

### Test the Updated API

```bash
# Run the supplier integration test
python test_supplier_integration.py
```

### Example Test Case

```python
import_slip_data = {
    "supplier_id": "recSupplier001",
    "import_type": "Nhập mua",
    "import_slip_details": [
        {
            "product_id": "recProduct001",
            "unit_conversions_id": "recUnitConv001",  # Required field
            "quantity": 50,
            "unit_price": 450000,
            "vat": 8.0
        }
    ]
}
```

## Summary

The Import Slip API has been successfully updated to include **required unit conversion tracking**. This enhancement provides:

- ✅ **Proper unit standardization** in import operations
- ✅ **Consistent data structure** across all transaction types
- ✅ **Enhanced inventory accuracy** with unit-specific tracking
- ✅ **Better business intelligence** capabilities

All import slip operations now properly link to unit conversions for complete inventory management! 📦⚖️
