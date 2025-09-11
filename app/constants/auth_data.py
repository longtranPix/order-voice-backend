from app.core.config import settings

# Table name mappings for template-based database creation
TABLE_NAME_MAPPING = {
    # "Khách Hàng": "table_customer_id",
    # "Đơn Vị Tính Chuyển Đổi": "table_unit_conversions_id",
    # "Thương Hiệu": "table_brand_id",
    # "Sản Phẩm": "table_product_id",
    "Chi Tiết Đơn Hàng": "table_order_detail_id",
    "Đơn Hàng": "table_order_id",
    # "Thông Tin Hóa Đơn": "table_invoice_info_id",
    # "Chi Tiết Phiếu Nhập": "table_import_slip_details_id",
    # "Chi Tiết Phiếu Xuất": "table_delivery_note_details_id",
    # "Phiếu Xuất": "table_delivery_note_id",
    # "Nhà Cung Cấp": "table_supplier_id",
    # "Phiếu Nhập": "table_import_slip_id",
    # "Danh Mục": "table_catalog_id",
    # "Ngành Hàng": "table_product_line_id",
    # "Thuộc Tính": "table_attribute_id",
    # "Tên Thuộc Tính": "table_attribute_type_id"
}

# Template ID for database creation
TEMPLATE_ID = settings.TEABLE_TEMPLATE_ID

# VietQR API configuration
VIETQR_BASE_URL = settings.VIETQR_BASE_URL

# Password encoding constants
PASSWORD_PREFIX = settings.PASSWORD_PREFIX
PASSWORD_SUFFIX = settings.PASSWORD_SUFFIX
SECRET_KEY_PREFIX = settings.SECRET_KEY_PREFIX
SALT_PREFIX = settings.SALT_PREFIX
