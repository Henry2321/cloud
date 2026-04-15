#!/bin/bash

set -e

OUTPUT_FILE="cspm_backend_payload.zip"
BUILD_DIR="build_temp"

echo "=== BẮT ĐẦU ĐÓNG GÓI CODE BACKEND CHO AWS LAMBDA ==="

echo "1. Dọn dẹp môi trường cũ..."
rm -rf $BUILD_DIR
rm -f $OUTPUT_FILE

echo "2. Tạo thư mục build tạm thời..."
mkdir $BUILD_DIR

echo "3. Copy mã nguồn ứng dụng..."
cp -r api/ $BUILD_DIR/api/
cp -r core/ $BUILD_DIR/core/
cp -r scanners/ $BUILD_DIR/scanners/
cp -r notifications/ $BUILD_DIR/notifications/
cp -r remediations/ $BUILD_DIR/remediations/

echo "4. Đang nén thành file $OUTPUT_FILE..."
cd $BUILD_DIR
python -m zipfile -c ../$OUTPUT_FILE .
cd ..

echo "5. Dọn dẹp thư mục tạm..."
rm -rf $BUILD_DIR

echo "=== HOÀN TẤT! ==="
echo "Đã tạo thành công file: $OUTPUT_FILE"
