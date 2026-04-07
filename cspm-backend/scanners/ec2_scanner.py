# Quét lỗi máy chủ EC2 (Mở port 22/3389 ra Internet)
from core.config import logger
from core.aws_connection import get_boto3_client
from core.database_adapter import save_finding
from notifications.alert_manager import send_security_alert

def scan_ec2_security_groups():
    logger.info("Bắt đầu quét EC2 Security Groups...")
    try:
        ec2_client = get_boto3_client('ec2')
        response = ec2_client.describe_security_groups()
        security_groups = response.get('SecurityGroups', [])

        for sg in security_groups:
            sg_id = sg['GroupId']
            sg_name = sg.get('GroupName', sg_id)
            sg_arn = f"arn:aws:ec2:::security-group/{sg_id}"

            is_pass = True
            details = f"Security Group {sg_name} được cấu hình an toàn."
            severity = 'LOW'

            for rule in sg.get('IpPermissions', []):
                from_port = rule.get('FromPort', 0)
                to_port = rule.get('ToPort', 65535)
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        if from_port <= 22 <= to_port or from_port <= 3389 <= to_port:
                            is_pass = False
                            details = f"Security Group {sg_name} đang mở port SSH/RDP ra Internet (0.0.0.0/0)!"
                            severity = 'CRITICAL'
                            break
                if not is_pass:
                    break

            finding = save_finding(
                service='EC2',
                resource_name=sg_name,
                resource_id=sg_arn,
                rule_name='EC2_SG_SSH_RDP_OPEN',
                is_pass=is_pass,
                severity=severity,
                details=details
            )

            if not is_pass:
                send_security_alert(finding)

    except Exception as e:
        logger.error(f"Lỗi hệ thống khi chạy EC2 Scanner: {e}")