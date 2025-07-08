# Bảng Dữ Liệu Được Tạo Khi Đăng Ký

## Tổng Quan

Khi người dùng đăng ký tài khoản mới trong hệ thống, hệ thống sẽ tự động tạo một không gian làm việc (workspace) hoàn chỉnh với tất cả các bảng dữ liệu cần thiết để quản lý hoạt động kinh doanh. Tài liệu này mô tả chi tiết về cấu trúc và chức năng của từng bảng.

## Danh Sách Bảng Được Tạo

### 1. 👥 **Bảng Khách Hàng (Customer Table)**

**Tên bảng:** `Khách Hàng`  
**Mô tả:** Quản lý thông tin khách hàng  
**Icon:** 👤

#### Các Trường Dữ Liệu:
- **Số khách hàng** (`customer_number`) - Tự động tăng
- **Tên khách hàng** (`customer_name`) - Văn bản dài
- **Số điện thoại** (`phone`) - Văn bản một dòng
- **Email** (`email`) - Văn bản một dòng
- **Địa chỉ** (`address`) - Văn bản dài

#### Chức Năng:
- Lưu trữ thông tin chi tiết khách hàng
- Tự động tạo mã khách hàng duy nhất
- Liên kết với đơn hàng và phiếu xuất

---

### 2. ⚖️ **Bảng Đơn Vị Tính Chuyển Đổi (Unit Conversions Table)**

**Tên bảng:** `Đơn Vị Tính Chuyển Đổi`  
**Mô tả:** Quản lý các đơn vị tính và tỷ lệ chuyển đổi  
**Icon:** ⚖️

#### Các Trường Dữ Liệu:
- **Tên đơn vị** (`name_unit`) - Văn bản một dòng
- **Hệ số chuyển đổi** (`conversion_factor`) - Số
- **Đơn vị mặc định** (`unit_default`) - Văn bản một dòng
- **Giá bán** (`price`) - Số
- **VAT (%)** (`vat`) - Số

#### Chức Năng:
- Định nghĩa các đơn vị tính (chai, lốc, thùng, kg, tấn...)
- Thiết lập tỷ lệ chuyển đổi giữa các đơn vị
- Quản lý giá bán theo từng đơn vị
- Cấu hình VAT cho từng đơn vị

---

### 3. 🛍️ **Bảng Sản Phẩm (Product Table)**

**Tên bảng:** `Sản Phẩm`  
**Mô tả:** Quản lý thông tin sản phẩm  
**Icon:** 📦

#### Các Trường Dữ Liệu:
- **Mã sản phẩm** (`product_code`) - Công thức tự động
- **Tên sản phẩm** (`product_name`) - Văn bản dài
- **Đơn vị tính** (`unit_conversions`) - Liên kết đa chiều đến bảng Đơn Vị Tính
- **Tổng nhập** (`total_imported`) - Rollup từ chi tiết phiếu nhập
- **Tổng xuất** (`total_delivered`) - Rollup từ chi tiết phiếu xuất
- **Tồn kho hiện tại** (`current_inventory`) - Công thức (Tổng nhập - Tổng xuất)

#### Chức Năng:
- Quản lý danh mục sản phẩm
- Tự động tạo mã sản phẩm
- Liên kết với nhiều đơn vị tính
- Tự động tính toán tồn kho
- Theo dõi lịch sử nhập/xuất

---

### 4. 🧾 **Bảng Chi Tiết Đơn Hàng (Order Details Table)**

**Tên bảng:** `Chi Tiết Hoá Đơn`  
**Mô tả:** Chi tiết từng sản phẩm trong đơn hàng  
**Icon:** 🧾

#### Các Trường Dữ Liệu:
- **Số đơn hàng chi tiết** (`number_order_detail`) - Tự động tăng
- **Sản phẩm** (`product_link`) - Liên kết đến bảng Sản Phẩm (isOneWay: true)
- **Đơn vị tính** (`unit_conversions`) - Liên kết đến bảng Đơn Vị Tính (isOneWay: true)
- **Đơn giá** (`unit_price`) - Số
- **Số lượng** (`quantity`) - Số
- **VAT** (`vat`) - Số
- **Tạm tính** (`temp_total`) - Số
- **Thành tiền** (`final_total`) - Số

#### Đặc Điểm:
- **isOneWay: true** - Chỉ áp dụng cho bảng này
- Không tạo liên kết ngược về bảng sản phẩm
- Tập trung vào quản lý đơn hàng

---

### 5. 📦 **Bảng Đơn Hàng (Order Table)**

**Tên bảng:** `Đơn Hàng`  
**Mô tả:** Quản lý thông tin đơn hàng  
**Icon:** 📦

#### Các Trường Dữ Liệu:
- **Số đơn hàng** (`order_number`) - Công thức tự động (DH-DDMMYYYY-XXX)
- **Khách hàng** (`customer_link`) - Liên kết đến bảng Khách Hàng
- **Chi tiết hóa đơn** (`invoice_details`) - Liên kết đến bảng Chi Tiết Đơn Hàng
- **Xuất hóa đơn** (`invoice_state`) - Checkbox
- **Tổng tạm tính** (`total_temp`) - Số
- **Tổng VAT** (`total_vat`) - Số
- **Tổng sau VAT** (`total_after_vat`) - Số
- **Mã hóa đơn** (`invoice_code`) - Văn bản một dòng
- **File hóa đơn** (`invoice_file`) - Đính kèm

#### Chức Năng:
- Tự động tạo số đơn hàng theo định dạng
- Liên kết với khách hàng và chi tiết
- Quản lý trạng thái xuất hóa đơn
- Lưu trữ file hóa đơn

---

### 6. 📄 **Bảng Thông Tin Hóa Đơn (Invoice Info Table)**

**Tên bảng:** `Thông Tin Hoá Đơn`  
**Mô tả:** Cấu hình thông tin xuất hóa đơn  
**Icon:** 📄

#### Các Trường Dữ Liệu:
- **Loại hóa đơn** (`invoice_type`) - Văn bản một dòng
- **Mã mẫu** (`template_code`) - Văn bản một dòng
- **Ký hiệu** (`invoice_series`) - Văn bản một dòng
- **URL tạo hóa đơn** (`create_invoice_url`) - Văn bản dài
- **URL lấy PDF** (`get_pdf_url`) - Văn bản dài
- **Username** (`username`) - Văn bản một dòng
- **Password** (`password`) - Văn bản một dòng

#### Chức Năng:
- Cấu hình thông tin kết nối API hóa đơn
- Lưu trữ thông tin xác thực
- Quản lý mẫu hóa đơn

---

### 7. 📝 **Bảng Chi Tiết Phiếu Nhập (Import Slip Details Table)**

**Tên bảng:** `Chi Tiết Phiếu Nhập`  
**Mô tả:** Chi tiết từng sản phẩm trong phiếu nhập  
**Icon:** 📝

#### Các Trường Dữ Liệu:
- **Số chi tiết phiếu nhập** (`number_detail`) - Tự động tăng
- **Sản phẩm** (`product_link`) - Liên kết đến bảng Sản Phẩm (bidirectional)
- **Đơn vị tính** (`unit_conversions`) - Liên kết đến bảng Đơn Vị Tính (bidirectional)
- **Đơn giá** (`unit_price`) - Số
- **Số lượng** (`quantity`) - Số
- **VAT** (`vat`) - Số
- **Tạm tính** (`temp_total`) - Số
- **Thành tiền** (`final_total`) - Số

#### Đặc Điểm:
- Liên kết hai chiều với bảng sản phẩm
- Cho phép theo dõi lịch sử nhập hàng từ sản phẩm

---

### 8. 📤 **Bảng Chi Tiết Phiếu Xuất (Delivery Note Details Table)**

**Tên bảng:** `Chi Tiết Phiếu Xuất`  
**Mô tả:** Chi tiết từng sản phẩm trong phiếu xuất  
**Icon:** 📤

#### Các Trường Dữ Liệu:
- **Số chi tiết phiếu xuất** (`number_detail`) - Tự động tăng
- **Sản phẩm** (`product_link`) - Liên kết đến bảng Sản Phẩm (bidirectional)
- **Đơn vị tính** (`unit_conversions`) - Liên kết đến bảng Đơn Vị Tính (bidirectional)
- **Đơn giá** (`unit_price`) - Số
- **Số lượng** (`quantity`) - Số
- **VAT** (`vat`) - Số
- **Tạm tính** (`temp_total`) - Số
- **Thành tiền** (`final_total`) - Số

#### Đặc Điểm:
- Liên kết hai chiều với bảng sản phẩm
- Cho phép theo dõi lịch sử xuất hàng từ sản phẩm

---

### 9. 📤 **Bảng Phiếu Xuất (Delivery Note Table)**

**Tên bảng:** `Phiếu Xuất`  
**Mô tả:** Quản lý phiếu xuất kho  
**Icon:** 📤

#### Các Trường Dữ Liệu:
- **Số phiếu xuất** (`delivery_note_number`) - Công thức tự động (PX-DDMMYYYY-XXX)
- **Khách hàng** (`customer_link`) - Liên kết đến bảng Khách Hàng
- **Chi tiết phiếu xuất** (`delivery_note_details`) - Liên kết đến bảng Chi Tiết Phiếu Xuất
- **Đơn hàng** (`order_link`) - Liên kết đến bảng Đơn Hàng
- **Loại xuất** (`delivery_type`) - Văn bản một dòng
- **Tổng số lượng** (`total_quantity`) - Số
- **Tổng tiền** (`total_amount`) - Số

#### Chức Năng:
- Tự động tạo số phiếu xuất
- Liên kết với đơn hàng gốc
- Quản lý xuất kho

---

### 10. 📥 **Bảng Phiếu Nhập (Import Slip Table)**

**Tên bảng:** `Phiếu Nhập`  
**Mô tả:** Quản lý phiếu nhập kho  
**Icon:** 📥

#### Các Trường Dữ Liệu:
- **Số phiếu nhập** (`import_slip_number`) - Công thức tự động (PN-DDMMYYYY-XXX)
- **Nhà cung cấp** (`supplier_name`) - Văn bản một dòng
- **Chi tiết phiếu nhập** (`import_slip_details`) - Liên kết đến bảng Chi Tiết Phiếu Nhập
- **Ngày nhập** (`import_date`) - Ngày tháng
- **Tổng số lượng** (`total_quantity`) - Số
- **Tổng tiền** (`total_amount`) - Số

#### Chức Năng:
- Tự động tạo số phiếu nhập
- Quản lý nhập kho từ nhà cung cấp
- Theo dõi lịch sử nhập hàng

---

## Mối Quan Hệ Giữa Các Bảng

### 🔗 **Sơ Đồ Quan Hệ:**

```
Khách Hàng
├── → Đơn Hàng (một-nhiều)
└── → Phiếu Xuất (một-nhiều)

Sản Phẩm
├── ← Chi Tiết Đơn Hàng (một chiều từ đơn hàng)
├── ↔ Chi Tiết Phiếu Nhập (hai chiều)
└── ↔ Chi Tiết Phiếu Xuất (hai chiều)

Đơn Vị Tính Chuyển Đổi
├── ↔ Sản Phẩm (nhiều-nhiều)
├── ← Chi Tiết Đơn Hàng (một chiều từ đơn hàng)
├── ↔ Chi Tiết Phiếu Nhập (hai chiều)
└── ↔ Chi Tiết Phiếu Xuất (hai chiều)

Đơn Hàng
├── → Chi Tiết Đơn Hàng (một-nhiều)
└── → Phiếu Xuất (một-một)
```

### 🎯 **Đặc Điểm Quan Hệ:**

**isOneWay: true (Chỉ áp dụng cho Chi Tiết Đơn Hàng):**
- Chi tiết đơn hàng → Sản phẩm (một chiều)
- Chi tiết đơn hàng → Đơn vị tính (một chiều)
- Không tạo liên kết ngược về bảng sản phẩm

**Bidirectional (Áp dụng cho Phiếu Nhập/Xuất):**
- Chi tiết phiếu nhập ↔ Sản phẩm (hai chiều)
- Chi tiết phiếu xuất ↔ Sản phẩm (hai chiều)
- Cho phép theo dõi lịch sử từ bảng sản phẩm

---

## Quy Trình Tạo Bảng Khi Đăng Ký

### 📋 **Thứ Tự Tạo Bảng:**

1. **Bảng Khách Hàng** - Tạo đầu tiên
2. **Bảng Đơn Vị Tính Chuyển Đổi** - Tạo trước sản phẩm
3. **Bảng Sản Phẩm** - Liên kết với đơn vị tính
4. **Bảng Chi Tiết Đơn Hàng** - Liên kết với sản phẩm và đơn vị tính
5. **Bảng Đơn Hàng** - Liên kết với khách hàng và chi tiết
6. **Bảng Thông Tin Hóa Đơn** - Cấu hình độc lập
7. **Bảng Chi Tiết Phiếu Nhập** - Liên kết với sản phẩm
8. **Bảng Chi Tiết Phiếu Xuất** - Liên kết với sản phẩm
9. **Bảng Phiếu Xuất** - Liên kết với khách hàng, chi tiết và đơn hàng
10. **Bảng Phiếu Nhập** - Liên kết với chi tiết phiếu nhập

### ⚙️ **Cấu Hình Tự Động:**

- **Rollup Fields:** Tự động tính tổng nhập/xuất cho sản phẩm
- **Formula Fields:** Tự động tính tồn kho hiện tại
- **Lookup Fields:** Tự động lấy thông tin từ bảng liên kết
- **Auto Number:** Tự động tạo mã số cho các bảng

---

## Lợi Ích Của Cấu Trúc Bảng

### ✅ **Quản Lý Toàn Diện:**
- Hệ thống bảng hoàn chỉnh cho hoạt động kinh doanh
- Tự động tạo tất cả bảng cần thiết khi đăng ký
- Cấu trúc dữ liệu chuẩn và nhất quán

### ✅ **Tính Toán Tự Động:**
- Tự động tính tổng tiền, VAT, tồn kho
- Rollup và Formula fields giảm thiểu lỗi tính toán
- Cập nhật real-time khi có thay đổi dữ liệu

### ✅ **Truy Xuất Nguồn Gốc:**
- Theo dõi đầy đủ lịch sử nhập/xuất sản phẩm
- Liên kết rõ ràng giữa đơn hàng và phiếu xuất
- Audit trail hoàn chỉnh cho mọi giao dịch

### ✅ **Tối Ưu Hiệu Suất:**
- isOneWay cho đơn hàng giảm tải cho bảng sản phẩm
- Bidirectional cho nhập/xuất hỗ trợ báo cáo tồn kho
- Cấu trúc quan hệ phù hợp với từng nghiệp vụ

Hệ thống tự động tạo **10 bảng dữ liệu** hoàn chỉnh với **hơn 50 trường dữ liệu** và **nhiều mối quan hệ phức tạp** để đáp ứng đầy đủ nhu cầu quản lý kinh doanh! 🎯📊
