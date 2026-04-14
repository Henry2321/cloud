# Chuyên xử lý lệnh CRUD (Thêm, Đọc, Xóa) với Amazon DynamoDB
import uuid
from datetime import datetime
from core.config import DYNAMODB_TABLE, logger
from core.aws_connection import get_boto3_resource

# Tối ưu hóa cho Serverless (Cold Start): Khởi tạo kết nối DB ở ngoài hàm (Global scope)
# Để các lần chạy tiếp theo của Lambda sẽ tái sử dụng lại kết nối này, giúp app chạy nhanh hơn.
try:
    dynamodb = get_boto3_resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
except Exception as e:
    logger.error(f"Không thể kết nối tới bảng database {DYNAMODB_TABLE}. Lỗi: {e}")

def save_finding(service, resource_name, resource_id, rule_name, is_pass, severity, details):
    """
    Hàm chuẩn hóa và lưu trữ kết quả quét của 1 tài nguyên vào Database.
    """
    # Dùng composite key cố định để scan lại sẽ overwrite thay vì tạo bản ghi mới
    finding_id = f"{service}#{resource_id}#{rule_name}"
    timestamp = datetime.utcnow().isoformat()
    # Gán nhãn đạt/rớt
    status = 'PASS' if is_pass else 'FAIL'
    
    # Gom dữ liệu thành 1 khối JSON (Dictionary)
    item = {
        'id': finding_id,
        'timestamp': timestamp,
        'service': service,                  # VD: 'S3', 'EC2', 'IAM'
        'resource_name': resource_name,      # VD: 'my-secret-bucket-01'
        'resource_id': resource_id,          # VD: 'arn:aws:s3:::my-secret-bucket-01'
        'rule_name': rule_name,              # VD: 'S3_Block_Public_Access'
        'status': status,
        'severity': severity,                # VD: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
        'details': details                   # Câu văn giải thích lý do lỗi
    }
    
    try:
        # Lệnh bắn dữ liệu vào DynamoDB
        table.put_item(Item=item)
        
        # In log ra màn hình console để Admin dễ theo dõi
        if status == 'FAIL':
            logger.warning(f"❌ PHÁT HIỆN LỖI: {service} - {resource_name} (Luật: {rule_name})")
        else:
            logger.info(f"✅ AN TOÀN: {service} - {resource_name}")
            
        return item
        
    except Exception as e:
        logger.error(f"Lỗi khi cố gắng ghi dữ liệu vào DynamoDB: {e}")
        raise