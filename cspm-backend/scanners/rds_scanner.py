# Quét lỗi Database (Database bị public ra ngoài)
from core.config import logger
from core.aws_connection import get_boto3_client
from core.database_adapter import save_finding
from notifications.alert_manager import send_security_alert

def scan_rds_public_access():
    logger.info("Bắt đầu quét các cụm Database RDS...")
    try:
        rds_client = get_boto3_client('rds')
        response = rds_client.describe_db_instances()
        db_instances = response.get('DBInstances', [])
        
        for db in db_instances:
            db_identifier = db['DBInstanceIdentifier']
            db_arn = db['DBInstanceArn']
            
            # Lấy cờ PubliclyAccessible
            is_public = db.get('PubliclyAccessible', False)
            
            # Trạng thái an toàn là khi is_public == False
            is_pass = not is_public 
            
            if is_pass:
                details = "Database được cấu hình an toàn trong mạng nội bộ (Private)."
                severity = 'LOW'
            else:
                details = f"CẢNH BÁO: Database {db_identifier} đang bị mở Public ra Internet. Hãy tắt ngay cờ PubliclyAccessible!"
                severity = 'CRITICAL'
                
            # Lưu biên bản
            finding = save_finding(
                service='RDS',
                resource_name=db_identifier,
                resource_id=db_arn,
                rule_name='RDS_Public_Access_Prohibited',
                is_pass=is_pass,
                severity=severity,
                details=details
            )
            
            # Gửi báo động nếu hở DB
            if not is_pass:
                send_security_alert(finding)
                
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi chạy RDS Scanner: {e}")