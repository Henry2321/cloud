# Đọc biến môi trường do Terraform truyền vào (tên Bảng DynamoDB, v.v.)
import os
import logging

# 1. Cấu hình Logging (Rất quan trọng để xem lỗi trên AWS CloudWatch)
# Mặc định là INFO, có thể đổi thành DEBUG nếu muốn xem chi tiết
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logger = logging.getLogger('cspm_core')
logger.setLevel(LOG_LEVEL)

# 2. Cấu hình các dịch vụ AWS
# Lấy tên bảng từ biến môi trường, nếu không có thì dùng tên mặc định để test local
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'cspm-findings-table')

# Lấy Region hiện tại (ví dụ: us-east-1, ap-southeast-1)
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Cái LOL BIẾT LA (LOA)
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')