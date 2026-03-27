#!/bin/bash

# Dừng script ngay lập tức nếu có bất kỳ lệnh nào bị lỗi
set -e

# Tên của file zip sẽ được tạo ra
OUTPUT_FILE="cspm_backend_payload.zip"
BUILD_DIR="build_temp"

echo "=== BẮT ĐẦU ĐÓNG GÓI CODE BACKEND CHO AWS LAMBDA ==="

# 1. Dọn dẹp các file cũ của lần build trước (nếu có)
echo "1. Dọn dẹp môi trường cũ..."
rm -rf $BUILD_DIR
rm -f $OUTPUT_FILE

# 2. Tạo thư mục tạm thời để gom đồ
echo "2. Tạo thư mục build tạm thời..."
mkdir $BUILD_DIR

# 3. Cài đặt thư viện (dependencies) vào thư mục tạm
echo "3. Cài đặt thư viện từ requirements.txt..."
# Lệnh pip với cờ -t (--target) ép Python tải thư viện thẳng vào thư mục build_temp
pip install -r requirements.txt -t $BUILD_DIR/

# 4. Copy mã nguồn của dự án vào thư mục tạm
echo "4. Copy mã nguồn ứng dụng..."
cp -r api/ $BUILD_DIR/api/
cp -r core/ $BUILD_DIR/core/
cp -r scanners/ $BUILD_DIR/scanners/
cp -r notifications/ $BUILD_DIR/notifications/
cp -r remediations/ $BUILD_DIR/remediations/

# Chú ý: Chúng ta KHÔNG copy thư mục `tests/` vì AWS Lambda không cần chạy test, 
# bỏ đi sẽ giúp file zip nhẹ hơn, Lambda khởi động nhanh hơn!

# 5. Nén toàn bộ thành file .zip
echo "5. Đang nén thành file $OUTPUT_FILE..."
cd $BUILD_DIR
# Nén tất cả mọi thứ trong thư mục hiện tại (.)
python -m zipfile -c ../$OUTPUT_FILE .
cd ..

# 6. Dọn dẹp rác
echo "6. Dọn dẹp thư mục tạm..."
rm -rf $BUILD_DIR

echo "=== HOÀN TẤT! ==="
echo "Đã tạo thành công file: $OUTPUT_FILE"
echo "Terraform bây giờ có thể lấy file này để mang lên AWS."

