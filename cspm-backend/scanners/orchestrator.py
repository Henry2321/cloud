import json
from core.config import logger
from scanners.s3_scanner import scan_s3_public_access
from scanners.ec2_scanner import scan_ec2_security_groups
from scanners.iam_scanner import scan_iam_users
from scanners.rds_scanner import scan_rds_public_access

# BỘ HEADER BẮT BUỘC ĐỂ TRÌNH DUYỆT (REACT) KHÔNG CHẶN API
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}

def lambda_handler(event, context):
    """
    Hàm này được kích hoạt bởi Amazon EventBridge (Cron job) hoặc API Gateway (Nút Scan Now)
    """
    logger.info("=== BẮT ĐẦU CHIẾN DỊCH QUÉT CSPM TOÀN HỆ THỐNG ===")
    
    try:
        # Gọi các hàm quét lỗi
        scan_s3_public_access()
        scan_ec2_security_groups()
        scan_iam_users()
        scan_rds_public_access()
        
        logger.info("=== HOÀN TẤT CHIẾN DỊCH QUÉT ===")
        
        # TRẢ VỀ THÀNH CÔNG CHO FRONTEND REACT (Kèm Headers)
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                "message": "Quá trình quét bảo mật đã hoàn tất thành công!",
                "status": "success"
            })
        }
        
    except Exception as e:
        logger.error(f"Chiến dịch quét bị gián đoạn do lỗi: {e}")
        
        # TRẢ VỀ LỖI CHO FRONTEND REACT (Cũng phải kèm Headers)
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                "message": f"Lỗi hệ thống: {str(e)}",
                "status": "error"
            })
        }