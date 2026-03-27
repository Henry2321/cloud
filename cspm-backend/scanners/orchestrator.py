# Hàm Lambda "Đội trưởng": Được EventBridge gọi mỗi ngày để kích hoạt các hàm quét bên dưới
import json
from core.config import logger
from scanners.s3_scanner import scan_s3_public_access
from scanners.ec2_scanner import scan_ec2_security_groups
from scanners.iam_scanner import scan_iam_users
from scanners.rds_scanner import scan_rds_public_access
# Nếu bạn làm thêm IAM thì import thêm vào đây:
# from scanners.iam_scanner import scan_iam_users

def lambda_handler(event, context):
    """
    Hàm này được kích hoạt bởi Amazon EventBridge (Cron job).
    """
    logger.info("=== BẮT ĐẦU CHIẾN DỊCH QUÉT CSPM TOÀN HỆ THỐNG ===")
    
    try:
        scan_s3_public_access()
        scan_ec2_security_groups()
        scan_iam_users()         # <--- GỌI ĐỘI QUÉT IAM
        scan_rds_public_access() # <--- GỌI ĐỘI QUÉT DATABASE
        
        logger.info("=== HOÀN TẤT CHIẾN DỊCH QUÉT ===")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Quá trình quét bảo mật đã hoàn tất thành công!')
        }
        
    except Exception as e:
        logger.error(f"Chiến dịch quét bị gián đoạn do lỗi: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Lỗi hệ thống: {e}')
        }