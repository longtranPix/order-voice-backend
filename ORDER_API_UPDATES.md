# Create Order API Updates

## Overview

The Create Order API has been updated to simplify the input requirements and remove unnecessary fields. The API now automatically retrieves table IDs from user information and no longer requires notes in the request.

## Changes Made

### ✅ **Removed Fields from Input:**

1. **`order_table_id`** - Removed from input (automatically retrieved from user table info)
2. **`detail_table_id`** - Removed from input (automatically retrieved from user table info)  
3. **`notes`** - Removed from input (no longer supported)

### ✅ **Simplified Request Schema:**

**Before:**
```json
{
  "customer_id": "recCustomer001",
  "order_details": [...],
  "delivery_type": "Xuất bán",
  "notes": "Optional notes",
  "order_table_id": "tblOrder123",
  "detail_table_id": "tblOrderDetail456"
}
```

**After:**
```json
{
  "customer_id": "recCustomer001",
  "order_details": [...],
  "delivery_type": "Xuất bán"
}
```

### ✅ **Automatic Table ID Retrieval:**

The API now automatically retrieves the required table IDs from the user's table information using their access token:

```javascript
// Get user table information
user_info = await get_user_table_info(current_user)

// Extract required table IDs
order_table_id = user_info.get("table_order_id")
order_detail_table_id = user_info.get("table_order_detail_id")
```

## Updated API Specification

### **Endpoint:** `POST /orders/create-order`

### **Request Schema:**
```json
{
  "customer_id": "string",
  "order_details": [
    {
      "product_id": "string",
      "unit_conversions_id": "string", 
      "unit_price": "number",
      "quantity": "number",
      "vat": "number"
    }
  ],
  "delivery_type": "string (default: 'Xuất bán')"
}
```

### **Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customer_id` | string | Yes | ID of the customer from customer table |
| `order_details` | array | Yes | Array of order detail items |
| `order_details[].product_id` | string | Yes | ID of the product from product table |
| `order_details[].unit_conversions_id` | string | Yes | ID of unit conversion for proper tracking |
| `order_details[].unit_price` | number | Yes | Unit price for this item |
| `order_details[].quantity` | number | Yes | Quantity ordered |
| `order_details[].vat` | number | Yes | VAT rate for this item |
| `delivery_type` | string | No | Type of delivery (default: "Xuất bán") |

### **Example Request:**
```json
{
  "customer_id": "recCustomer001",
  "order_details": [
    {
      "product_id": "recProduct001",
      "unit_conversions_id": "recUnitConv001",
      "unit_price": 15000,
      "quantity": 50,
      "vat": 10
    }
  ],
  "delivery_type": "Xuất bán"
}
```

### **Response Schema:**
```json
{
  "status": "success",
  "detail": "Đơn hàng và phiếu xuất đã được tạo thành công",
  "order_id": "recOrder001",
  "order_code": "DH-02012025-001",
  "delivery_note_id": "recDeliveryNote001",
  "delivery_note_code": "PX-02012025-001",
  "customer_id": "recCustomer001",
  "total_items": 1,
  "total_temp": 750000,
  "total_vat": 75000,
  "total_after_vat": 825000
}
```

## Benefits of Updates

### ✅ **Simplified Integration:**
- Fewer required fields in request
- No need to manage table IDs manually
- Cleaner API interface

### ✅ **Enhanced Security:**
- Table IDs retrieved from authenticated user context
- Prevents unauthorized access to other users' tables
- Automatic validation of user permissions

### ✅ **Better User Experience:**
- Less complex request structure
- Automatic handling of backend details
- Focus on business data only

### ✅ **Improved Maintainability:**
- Centralized table ID management
- Consistent user context handling
- Reduced API surface area

## Implementation Details

### **Files Updated:**

1. **`app/schemas/orders.py`**
   - Removed `notes` field from `CreateOrderRequest`
   - Removed unused `Optional` import

2. **`app/services/order_service.py`**
   - Updated delivery note creation to exclude notes
   - Table IDs now retrieved from user context

3. **`CREATE_ORDER_API.md`**
   - Updated documentation to reflect new schema
   - Removed references to notes field
   - Updated examples and field descriptions

4. **`API_DOCUMENTATION.md`**
   - Updated order creation examples
   - Removed notes from request examples

5. **`test_refactored_order_api.py`**
   - Updated test cases to exclude notes field

### **Backward Compatibility:**

⚠️ **Breaking Changes:**
- `notes` field is no longer accepted in requests
- `order_table_id` and `detail_table_id` are no longer required/accepted
- Existing integrations must be updated to use new schema

### **Migration Guide:**

**For existing API clients:**

1. **Remove table ID fields:**
   ```diff
   {
     "customer_id": "recCustomer001",
     "order_details": [...],
   - "order_table_id": "tblOrder123",
   - "detail_table_id": "tblOrderDetail456"
   }
   ```

2. **Remove notes field:**
   ```diff
   {
     "customer_id": "recCustomer001",
     "order_details": [...],
     "delivery_type": "Xuất bán"
   - "notes": "Optional notes"
   }
   ```

3. **Ensure proper authentication:**
   - API now relies on user token for table ID retrieval
   - Verify access token is valid and has proper permissions

## Testing

### **Updated Test Cases:**

The test files have been updated to reflect the new API structure:

```javascript
// Example test case
const orderData = {
  customer_id: "recCustomer001",
  order_details: [
    {
      product_id: "recProduct001",
      unit_conversions_id: "recUnitConv001",
      unit_price: 15000,
      quantity: 50,
      vat: 10
    }
  ],
  delivery_type: "Xuất bán"
  // notes field removed
  // table IDs removed
};
```

### **Test Coverage:**

- ✅ Order creation with simplified schema
- ✅ Automatic table ID retrieval
- ✅ Delivery note creation without notes
- ✅ Error handling for missing fields
- ✅ Authentication and authorization

## Summary

The Create Order API has been successfully simplified by:

1. **Removing unnecessary input fields** (`order_table_id`, `detail_table_id`, `notes`)
2. **Implementing automatic table ID retrieval** from user context
3. **Maintaining full functionality** while reducing complexity
4. **Updating all documentation and tests** to reflect changes

The API now provides a cleaner, more secure, and easier-to-use interface for order creation while maintaining all existing functionality for automatic delivery note generation and complete order fulfillment workflow.
