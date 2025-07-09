# Order Structure Clarification

## Overview

This document clarifies the implementation of `isOneWay` option in the table structure refactoring. The `isOneWay: true` option is applied **only to the order detail table**, not to import slip details or delivery note details tables.

## Table Structure Implementation

### ✅ **Order Detail Table (with isOneWay: true)**

```json
{
  "name": "Chi Tiết Hoá Đơn",
  "fields": [
    {"type": "autoNumber", "name": "Số đơn hàng chi tiết", "dbFieldName": "number_order_detail"},
    {
      "type": "link", 
      "name": "Sản phẩm", 
      "dbFieldName": "product_link",
      "options": {
        "foreignTableId": "product_table_id", 
        "relationship": "manyOne",
        "isOneWay": true  // ✅ Applied here
      }
    },
    {
      "type": "link", 
      "name": "Đơn vị tính", 
      "dbFieldName": "unit_conversions",
      "options": {
        "foreignTableId": "unit_conversion_table_id", 
        "relationship": "manyOne",
        "isOneWay": true  // ✅ Applied here
      }
    },
    {"type": "number", "name": "Đơn Giá", "dbFieldName": "unit_price"},
    {"type": "number", "name": "Số lượng", "dbFieldName": "quantity"},
    {"type": "number", "name": "VAT", "dbFieldName": "vat"},
    {"type": "number", "name": "Tạm Tính", "dbFieldName": "temp_total"},
    {"type": "number", "name": "Thành Tiền", "dbFieldName": "final_total"}
  ]
}
```

### ✅ **Import Slip Details Table (without isOneWay)**

```json
{
  "name": "Chi Tiết Phiếu Nhập",
  "fields": [
    {"type": "autoNumber", "name": "Số Chi Tiết Phiếu Nhập", "dbFieldName": "number_detail"},
    {
      "type": "link",
      "name": "Sản phẩm",
      "dbFieldName": "product_link",
      "options": {
        "foreignTableId": "product_table_id", 
        "relationship": "manyOne"
        // ❌ No isOneWay here - allows bidirectional relationship
      }
    },
    {
      "type": "link",
      "name": "Đơn vị tính",
      "dbFieldName": "unit_conversions",
      "options": {
        "foreignTableId": "unit_conversion_table_id", 
        "relationship": "manyOne"
        // ❌ No isOneWay here - allows bidirectional relationship
      }
    },
    {"type": "number", "name": "Đơn Giá", "dbFieldName": "unit_price"},
    {"type": "number", "name": "Số lượng", "dbFieldName": "quantity"},
    {"type": "number", "name": "VAT", "dbFieldName": "vat"},
    {"type": "number", "name": "Tạm Tính", "dbFieldName": "temp_total"},
    {"type": "number", "name": "Thành Tiền", "dbFieldName": "final_total"}
  ]
}
```

### ✅ **Delivery Note Details Table (without isOneWay)**

```json
{
  "name": "Chi Tiết Phiếu Xuất",
  "fields": [
    {"type": "autoNumber", "name": "Số Chi Tiết Phiếu Xuất", "dbFieldName": "number_detail"},
    {
      "type": "link",
      "name": "Sản phẩm",
      "dbFieldName": "product_link",
      "options": {
        "foreignTableId": "product_table_id", 
        "relationship": "manyOne"
        // ❌ No isOneWay here - allows bidirectional relationship
      }
    },
    {
      "type": "link",
      "name": "Đơn vị tính",
      "dbFieldName": "unit_conversions",
      "options": {
        "foreignTableId": "unit_conversion_table_id", 
        "relationship": "manyOne"
        // ❌ No isOneWay here - allows bidirectional relationship
      }
    },
    {"type": "number", "name": "Đơn Giá", "dbFieldName": "unit_price"},
    {"type": "number", "name": "Số lượng", "dbFieldName": "quantity"},
    {"type": "number", "name": "VAT", "dbFieldName": "vat"},
    {"type": "number", "name": "Tạm Tính", "dbFieldName": "temp_total"},
    {"type": "number", "name": "Thành Tiền", "dbFieldName": "final_total"}
  ]
}
```

## Rationale for isOneWay Implementation

### **Order Detail Table (isOneWay: true)**

**Why isOneWay is used:**
- Order details are typically viewed from the order perspective
- Prevents cluttering product and unit conversion tables with reverse links
- Simplifies the data model for order management
- Orders are temporary/transactional data

**Benefits:**
- ✅ Cleaner product table interface
- ✅ Simplified order management
- ✅ Reduced visual clutter in related tables
- ✅ Better performance for order operations

### **Import/Delivery Slip Details (isOneWay: false)**

**Why isOneWay is NOT used:**
- Import and delivery operations need bidirectional visibility
- Products need to show their import/delivery history
- Inventory tracking requires reverse relationships
- Business users need to see product movement history

**Benefits:**
- ✅ Product tables show import/delivery history
- ✅ Better inventory tracking and reporting
- ✅ Complete audit trail for product movements
- ✅ Enhanced business intelligence capabilities

## Database Relationship Diagram

```
Product Table
├── ← Import Slip Details (bidirectional)
├── ← Delivery Note Details (bidirectional)  
└── ← Order Details (one-way only)

Unit Conversions Table
├── ← Import Slip Details (bidirectional)
├── ← Delivery Note Details (bidirectional)
└── ← Order Details (one-way only)
```

## Business Impact

### **Order Management**
- Orders focus on customer transactions
- Clean interface without reverse relationship clutter
- Simplified order processing workflow

### **Inventory Management**
- Import/delivery operations maintain full traceability
- Products show complete movement history
- Enhanced reporting and analytics capabilities

### **Data Integrity**
- All tables maintain proper foreign key relationships
- Consistent field naming across all detail tables
- Proper calculation fields in all transactions

## Implementation Files

### **Updated Files:**
1. `app/constants/auth_data.py`
   - Order detail table: `isOneWay: true` for both link fields
   - Import slip details: No `isOneWay` option (bidirectional)
   - Delivery note details: No `isOneWay` option (bidirectional)

2. `test_updated_order_structure.py`
   - Updated test descriptions to reflect correct implementation
   - Clarified that `isOneWay` applies only to order details

### **Key Changes Made:**
- ✅ Removed `isOneWay: true` from import slip details table
- ✅ Removed `isOneWay: true` from delivery note details table
- ✅ Kept `isOneWay: true` only in order detail table
- ✅ Updated test documentation to reflect correct implementation

## Summary

The corrected implementation provides:

1. **Order Details**: One-way relationships for clean order management
2. **Import/Delivery Details**: Bidirectional relationships for complete traceability
3. **Consistent Structure**: All detail tables have same field structure
4. **Business Logic**: Appropriate relationship types for each use case

This approach balances clean order management with comprehensive inventory tracking and business intelligence capabilities.
