# Quét lỗi máy chủ EC2 (Mở port 22/3389 ra Internet)
from core.config import logger
from core.aws_connection import get_boto3_client
from core.database_adapter import save_finding
from notifications.alert_manager import send_security_alert

def scan_s3_public_access():
    logger.info("Bắt đầu quét S3 Buckets...")
    try:
        s3_client = get_boto3_client('s3')
        response = s3_client.list_buckets()
        buckets = response.get('Buckets', [])
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            bucket_arn = f"arn:aws:s3:::{bucket_name}"
            
            is_pass = False
            details = "Bucket chưa được khóa Public Access. Nguy cơ rò rỉ dữ liệu cực cao!"
            severity = 'CRITICAL'
            
            try:
                # Lấy cấu hình chặn Public
                config = s3_client.get_public_access_block(Bucket=bucket_name)
                blocks = config.get('PublicAccessBlockConfiguration', {})
                
                # Cần cả 4 cờ này là True thì mới an toàn 100%
                if all([
                    blocks.get('BlockPublicAcls'),
                    blocks.get('IgnorePublicAcls'),
                    blocks.get('BlockPublicPolicy'),
                    blocks.get('RestrictPublicBuckets')
                ]):
                    is_pass = True
                    details = "Bucket đã được cấu hình khóa an toàn."
                    severity = 'LOW'
                    
            except Exception as e:
                if 'NoSuchPublicAccessBlockConfiguration' in str(e):
                    # Không có cấu hình = Đang mở public
                    pass 
                else:
                    logger.error(f"Lỗi không xác định khi quét S3 {bucket_name}: {e}")
            
            # 1. Lưu kết quả vào DynamoDB
            finding = save_finding(
                service='S3',
                resource_name=bucket_name,
                resource_id=bucket_arn,
                rule_name='S3_Block_Public_Access',
                is_pass=is_pass,
                severity=severity,
                details=details
            )
            
            # 2. Nếu rớt (FAIL), lập tức hú còi báo động qua Email
            if not is_pass:
                send_security_alert(finding)
                
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi chạy S3 Scanner: {e}")