from core.config import logger
from core.aws_connection import get_boto3_client
from core.database_adapter import save_finding
from notifications.alert_manager import send_security_alert

def scan_iam_users():
    logger.info("Bắt đầu quét cấu hình IAM Users (MFA)...")
    try:
        iam_client = get_boto3_client('iam')
        response = iam_client.list_users()
        users = response.get('Users', [])
        
        for user in users:
            user_name = user['UserName']
            user_arn = user['Arn']
            
            is_pass = False
            details = f"Tài khoản {user_name} CHƯA bật xác thực 2 bước (MFA). Nguy cơ bị chiếm quyền rất cao!"
            severity = 'HIGH'
            
            try:
                mfa_response = iam_client.list_mfa_devices(UserName=user_name)
                mfa_devices = mfa_response.get('MFADevices', [])

                if len(mfa_devices) > 0:
                    is_pass = True
                    details = f"Tài khoản {user_name} đã bật MFA an toàn."
                    severity = 'LOW'
                else:
                    # Kiểm tra đã enforce CSPM_ForceMFA policy chưa
                    policies = iam_client.list_user_policies(UserName=user_name)
                    if 'CSPM_ForceMFA' in policies.get('PolicyNames', []):
                        is_pass = True
                        details = f"Tài khoản {user_name} đã được enforce MFA policy (CSPM_ForceMFA)."
                        severity = 'LOW'

            except Exception as e:
                logger.error(f"Lỗi khi kiểm tra MFA của user {user_name}: {e}")
            
            # Lưu biên bản
            finding = save_finding(
                service='IAM',
                resource_name=user_name,
                resource_id=user_arn,
                rule_name='IAM_User_MFA_Enabled',
                is_pass=is_pass,
                severity=severity,
                details=details
            )
            
            # Nếu vi phạm thì hú còi báo động
            if not is_pass:
                send_security_alert(finding)
                
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi chạy IAM Scanner: {e}")