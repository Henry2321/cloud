# Gửi tin nhắn qua Amazon SNS (Email) khi phát hiện lỗi mức Critical
import json
from core.config import SNS_TOPIC_ARN, logger
from core.aws_connection import get_boto3_client

def send_security_alert(finding):
    """
    Hàm định dạng và gửi cảnh báo qua Amazon SNS khi phát hiện lỗ hổng.
    Chỉ gửi cảnh báo với các lỗi có mức độ HIGH hoặc CRITICAL.
    """
    
    # Kiểm tra xem Terraform đã truyền địa chỉ (ARN) của SNS Topic vào chưa
    if not SNS_TOPIC_ARN:
        logger.warning("Không có cấu hình SNS_TOPIC_ARN. Bỏ qua bước gửi email cảnh báo.")
        return False
        
    # Lọc mức độ: Ví dụ chỉ gửi email nếu lỗi là HIGH hoặc CRITICAL để tránh spam Admin
    severity = finding.get('severity', 'LOW')
    if severity not in ['HIGH', 'CRITICAL']:
        logger.info(f"Lỗi mức {severity} - Không đủ nghiêm trọng để gửi email khẩn cấp.")
        return False

    try:
        # Lấy "bộ đàm" (client) để gọi cho dịch vụ SNS
        sns_client = get_boto3_client('sns')
        
        # 1. Soạn Tiêu đề Email (Subject)
        service = finding.get('service', 'AWS')
        subject = f"[CSPM CẢNH BÁO KHẨN CẤP] Phát hiện lỗ hổng {severity} trên {service}!"
        
        # 2. Soạn Nội dung Email (Body)
        message = f"""
Kính gửi Đội Quản trị Bảo mật (Security Team),

Hệ thống CSPM vừa phát hiện một lỗ hổng cấu hình nghiêm trọng trên AWS Account của bạn!

⚠️ THÔNG TIN CHI TIẾT:
--------------------------------------------------
- Dịch vụ vi phạm  : {service}
- Tên tài nguyên   : {finding.get('resource_name')}
- Luật vi phạm     : {finding.get('rule_name')}
- Mức độ nguy hiểm : {severity}
- Thời gian quét   : {finding.get('timestamp')} (UTC)

📝 MÔ TẢ LỖI:
{finding.get('details')}

🔧 HÀNH ĐỘNG YÊU CẦU:
Vui lòng đăng nhập vào AWS Console hoặc sử dụng CSPM Dashboard để kiểm tra và khắc phục lỗ hổng này ngay lập tức để tránh nguy cơ rò rỉ dữ liệu hoặc bị tấn công.
--------------------------------------------------
Tin nhắn này được gửi tự động từ Hệ thống CSPM Serverless.
"""
        
        # 3. Bắn tin nhắn đi
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject[:100], # AWS quy định Subject tối đa 100 ký tự
            Message=message
        )
        
        logger.info(f"📧 Đã gửi email cảnh báo thành công! Message ID: {response.get('MessageId')}")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khi cố gắng gửi cảnh báo qua SNS: {e}")
        return False