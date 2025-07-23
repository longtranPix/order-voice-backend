"""
Authentication hardcoded data and constants
"""

# Table payloads for signup process
CUSTOMER_TABLE_PAYLOAD = {
    "name": "Khách Hàng",
    "dbTableName": "customers",
    "description": "Bảng quản lý khách hàng",
    "icon": "👥",
    "fieldKeyType": "dbFieldName",
    "fields": [
        {
            "type": "singleLineText",
            "name": "Số điện thoại",
            "dbFieldName": "phone_number",
            "unique": True
        },
        {
            "type": "singleLineText",
            "name": "Họ và tên",
            "dbFieldName": "fullname"
        }
    ],
    "records": []
}

def get_order_detail_table_payload(product_table_id: str, unit_conversion_table_id: str) -> dict:
    """Get order detail table payload with dynamic table IDs"""
    return {
        "name": "Chi Tiết Đơn Hàng",
        "description": "Chi tiết đơn hàng",
        "icon": "🧾",
        "fields": [
            {"type": "autoNumber", "name": "Số đơn hàng chi tiết", "dbFieldName": "number_order_detail"},
            {
                "type": "link",
                "name": "Sản phẩm",
                "dbFieldName": "product_link",
                "options": {
                    "foreignTableId": product_table_id,
                    "relationship": "manyOne",
                    "isOneWay": True
                }
            },
            {
                "type": "link",
                "name": "Đơn vị tính",
                "dbFieldName": "unit_conversions",
                "options": {
                    "foreignTableId": unit_conversion_table_id,
                    "relationship": "manyOne",
                    "isOneWay": True
                }
            },
            {"type": "number", "name": "Đơn Giá", "dbFieldName": "unit_price"},
            {"type": "number", "name": "Số lượng", "dbFieldName": "quantity"},
            {"type": "number", "name": "VAT", "dbFieldName": "vat"}
        ],
        "fieldKeyType": "dbFieldName",
        "records": []
    }

def get_order_table_payload(customer_table_id: str, detail_table_id: str) -> dict:
    """Get order table payload with dynamic table IDs"""
    return {
        "name": "Đơn Hàng",
        "description": "Bảng lưu thông tin các đơn hàng",
        "icon": "📦",
        "fields": [
            {"type": "formula", "name": "Số đơn hàng", "dbFieldName": "order_number", "options": {"expression": "concatenate('DH-', DATETIME_FORMAT(CREATED_TIME(), 'DDMMYYYY'), '-', AUTO_NUMBER())"}},
            {"type": "link", "name": "Khách Hàng", "dbFieldName": "customer_link", "options": {"foreignTableId": customer_table_id, "relationship": "manyOne"}},
            {"type": "link", "name": "Chi Tiết Đơn Hàng", "dbFieldName": "order_details", "options": {"foreignTableId": detail_table_id, "relationship": "oneMany"}},
            {"type": "checkbox", "name": "Xuất hoá đơn", "dbFieldName": "invoice_state"},
            # {"type": "number", "name": "Tổng Tạm Tính", "dbFieldName": "total_temp"},
            # {"type": "number", "name": "Tổng VAT", "dbFieldName": "total_vat"},
            # {"type": "number", "name": "Tổng Sau VAT", "dbFieldName": "total_after_vat"},
            {"type": "singleLineText", "name": "Mã hoá đơn", "dbFieldName": "invoice_code"},
            {"type": "attachment", "name": "File hoá đơn", "dbFieldName": "invoice_file"}
        ],
        "fieldKeyType": "dbFieldName",
        "records": []
    }

INVOICE_INFO_TABLE_PAYLOAD = {
    "name": "Invoice Table",
    "dbTableName": "invoice_table",
    "description": "Bảng lưu thông tin hóa đơn",
    "icon": "🧾",
    "fields": [
        {"type": "singleLineText", "name": "Mã Hóa Đơn", "dbFieldName": "invoice_template", "description": "Trường mẫu chính", "unique": True},
        {"type": "singleLineText", "name": "Mã Mẫu", "dbFieldName": "template_code", "description": "Mã mẫu chính"},
        {"type": "multipleSelect", "name": "Sê-ri Hóa Đơn", "dbFieldName": "invoice_series", "description": "Nhiều sê-ri hóa đơn"}
    ],
    "fieldKeyType": "dbFieldName",
    "records": []
}

UNIT_CONVERSION_TABLE_PAYLOAD = {
    "name": "Đơn Vị Tính Chuyển Đổi",
    "dbTableName": "unit_conversions",
    "description": "Bảng quản lý đơn vị tính chuyển đổi",
    "icon": "⚖️",
    "fieldKeyType": "dbFieldName",
    "fields": [
        {
            "type": "singleLineText",
            "name": "Tên đơn vị",
            "dbFieldName": "name_unit"
        },
        {
            "type": "number",
            "name": "Hệ số chuyển đổi",
            "dbFieldName": "conversion_factor"
        },
        {
            "type": "singleLineText",
            "name": "Đơn vị mặc định",
            "dbFieldName": "unit_default"
        },
        {
            "type": "number",
            "name": "Giá đơn vị",
            "dbFieldName": "price"
        },
        {
            "type": "number",
            "name": "VAT(%)",
            "dbFieldName": "vat_rate"
        }
    ],
    "records": []
}

def get_product_table_payload(unit_conversion_table_id: str, brand_table_id: str) -> dict:
    """Get product table payload with unit conversion link"""
    return {
        "name": "Sản Phẩm",
        "dbTableName": "products",
        "description": "Bảng quản lý sản phẩm",
        "icon": "📦",
        "fieldKeyType": "dbFieldName",
        "fields": [
            {
                "type": "singleLineText",
                "name": "Tên sản phẩm",
                "dbFieldName": "product_name"
            },
            {
                "type": "link",
                "name": "Đơn vị tính",
                "dbFieldName": "unit_conversions",
                "options": {
                    "foreignTableId": unit_conversion_table_id,
                    "relationship": "manyMany"
                }
            },
            {
                "type": "link",
                "name": "Thương hiệu",
                "dbFieldName": "brand",
                "options": {
                    "foreignTableId": brand_table_id,
                    "relationship": "manyOne"
                }
            }
        ],
        "records": []
    }

def get_import_slip_details_payload(product_table_id: str, unit_conversion_table_id: str) -> dict:
    """Get import slip details table payload"""
    return {
        "name": "Chi Tiết Phiếu Nhập",
        "dbTableName": "import_slip_details",
        "description": "Bảng chi tiết phiếu nhập kho",
        "icon": "📝",
        "fieldKeyType": "dbFieldName",
        "fields": [
            {
                "type": "autoNumber",
                "name": "Số Chi Tiết Phiếu Nhập",
                "dbFieldName": "number_detail"
            },
            {
                "type": "link",
                "name": "Sản phẩm",
                "dbFieldName": "product_link",
                "options": {
                    "foreignTableId": product_table_id,
                    "relationship": "manyOne"
                }
            },
            {
                "type": "link",
                "name": "Đơn vị tính",
                "dbFieldName": "unit_conversions",
                "options": {
                    "foreignTableId": unit_conversion_table_id,
                    "relationship": "manyOne"
                }
            },
            {"type": "number", "name": "Đơn Giá", "dbFieldName": "unit_price"},
            {"type": "number", "name": "Số lượng", "dbFieldName": "quantity"},
            {"type": "number", "name": "VAT", "dbFieldName": "vat"}
        ],
        "records": []
    }

def get_delivery_note_details_payload(product_table_id: str, unit_conversion_table_id: str) -> dict:
    """Get delivery note details table payload"""
    return {
        "name": "Chi Tiết Phiếu Xuất",
        "dbTableName": "delivery_note_details",
        "description": "Bảng chi tiết phiếu xuất kho",
        "icon": "📤",
        "fieldKeyType": "dbFieldName",
        "fields": [
            {
                "type": "autoNumber",
                "name": "Số Chi Tiết Phiếu Xuất",
                "dbFieldName": "number_detail"
            },
            {
                "type": "link",
                "name": "Sản phẩm",
                "dbFieldName": "product_link",
                "options": {
                    "foreignTableId": product_table_id,
                    "relationship": "manyOne"
                }
            },
            {
                "type": "link",
                "name": "Đơn vị tính",
                "dbFieldName": "unit_conversions",
                "options": {
                    "foreignTableId": unit_conversion_table_id,
                    "relationship": "manyOne"
                }
            },
            {"type": "number", "name": "Số lượng", "dbFieldName": "quantity"}
        ],
        "records": []
    }

def get_delivery_note_payload(customer_table_id: str, delivery_note_details_id: str, order_table_id: str) -> dict:
    """Get delivery note table payload"""
    return {
        "name": "Phiếu Xuất",
        "dbTableName": "delivery_notes",
        "description": "Bảng quản lý phiếu xuất kho",
        "icon": "📤",
        "fieldKeyType": "dbFieldName",
        "fields": [
            {
                "type": "formula",
                "name": "Mã phiếu xuất",
                "dbFieldName": "delivery_note_code",
                "options": {
                    "expression": "concatenate('PX-', DATETIME_FORMAT(CREATED_TIME(), 'DDMMYYYY'), '-', AUTO_NUMBER())"
                }
            },
            {
                "type": "link",
                "name": "Chi tiết phiếu xuất",
                "dbFieldName": "delivery_note_details",
                "options": {"foreignTableId": delivery_note_details_id, "relationship": "oneMany"}
            },
            {
                "type": "link",
                "name": "Khách hàng",
                "dbFieldName": "customer_link",
                "options": {"foreignTableId": customer_table_id, "relationship": "manyOne"}
            },
            {
                "type": "link",
                "name": "Đơn Hàng",
                "dbFieldName": "order_link",
                "options": {"foreignTableId": order_table_id, "relationship": "manyOne"}
            },
            {
                "type": "singleSelect",
                "name": "Loại xuất",
                "dbFieldName": "delivery_type",
                "options": {
                    "choices": [
                        {"name": "Xuất bán"},
                        {"name": "Xuất trả"},
                        {"name": "Xuất mượn"}
                    ]
                }
            }
        ],
        "records": []
    }

def get_brand_table_payload() -> dict:
    """Get brand table payload"""
    return {
        "name": "Thương Hiệu",
        "description": "Bảng quản lý thương hiệu sản phẩm",
        "icon": "🔖",
        "fieldKeyType": "dbFieldName",
        "fields": [
            {"type": "singleLineText", "name": "Tên thương hiệu", "dbFieldName": "brand_name"}
        ],
        "records": []
    }

SUPPLIER_TABLE_PAYLOAD = {
    "name": "Nhà Cung Cấp",
    "description": "Quản lý thông tin nhà cung cấp",
    "icon": "🏭",
    "fields": [
        {"type": "autoNumber", "name": "Mã nhà cung cấp", "dbFieldName": "supplier_number"},
        {"type": "singleLineText", "name": "Tên nhà cung cấp", "dbFieldName": "supplier_name"},
        {"type": "longText", "name": "Địa chỉ", "dbFieldName": "address"}
    ],
    "fieldKeyType": "dbFieldName",
    "records": []
}

def get_import_slip_payload(import_slip_details_id: str, supplier_table_id: str) -> dict:
    """Get import slip table payload"""
    return {
        "name": "Phiếu Nhập",
        "dbTableName": "import_slips",
        "description": "Bảng quản lý phiếu nhập kho",
        "icon": "📥",
        "fieldKeyType": "dbFieldName",
        "fields": [
            {
                "type": "formula",
                "name": "Mã phiếu nhập",
                "dbFieldName": "import_slip_code",
                "options": {
                    "expression": "concatenate('PN-', DATETIME_FORMAT(CREATED_TIME(), 'DDMMYYYY'), '-', AUTO_NUMBER())"
                }
            },
            {
                "type": "link",
                "name": "Chi tiết phiếu nhập",
                "dbFieldName": "import_slip_details",
                "options": {"foreignTableId": import_slip_details_id, "relationship": "oneMany"}
            },
            {
                "type": "link",
                "name": "Nhà cung cấp",
                "dbFieldName": "supplier_link",
                "options": {"foreignTableId": supplier_table_id, "relationship": "manyOne"}
            },
            {
                "type": "singleSelect",
                "name": "Loại nhập",
                "dbFieldName": "import_type",
                "options": {
                    "choices": [
                        {"name": "Nhập mua"},
                        {"name": "Nhập trả"},
                        {"name": "Nhập điều chuyển"}
                    ]
                }
            }
        ],
        "records": []
    }

# API URLs and endpoints
VIETQR_API_BASE_URL = "https://api.vietqr.io/v2/business"

# Default values and constants
DEFAULT_INVOICE_EXPIRY_TIME = "2025-09-28"
DEFAULT_SPACE_NAME_SUFFIX = "_workspace"
DEFAULT_BASE_NAME_SUFFIX = "_base"

# Error messages
ERROR_MESSAGES = {
    "INVALID_TAXCODE": "Mã số thuế không hợp lệ hoặc không tồn tại",
    "USER_EXISTS": "Tài khoản đã tồn tại",
    "INVALID_CREDENTIALS": "Tên đăng nhập hoặc mật khẩu không đúng",
    "SPACE_CREATION_FAILED": "Không thể tạo không gian làm việc",
    "BASE_CREATION_FAILED": "Không thể tạo cơ sở dữ liệu",
    "TABLE_CREATION_FAILED": "Không thể tạo bảng",
    "TOKEN_GENERATION_FAILED": "Không thể tạo token truy cập"
}

# Success messages
SUCCESS_MESSAGES = {
    "SIGNUP_SUCCESS": "Tài khoản, không gian, cơ sở dữ liệu và tất cả các bảng đã được tạo thành công",
    "SIGNIN_SUCCESS": "Xác thực thành công"
}
