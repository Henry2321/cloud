# Code tự động xóa rule mở port 22 của Security Group
from core.config import logger
from core.aws_connection import get_boto3_client

def remove_open_ssh(security_group_id):
    """
    Hàm tự động xóa luật (rule) mở cổng 22 (SSH) ra toàn bộ Internet trên Security Group.
    """
    logger.info(f"Đang tiến hành tự động xóa port 22 đang hở trên Security Group: {security_group_id}")
    
    try:
        ec2_client = get_boto3_client('ec2')
        
        # Gọi API để gỡ bỏ (revoke) luật Ingress nguy hiểm
        ec2_client.revoke_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
        
        logger.info(f"✅ THÀNH CÔNG: Đã xóa rule chặn truy cập SSH công khai trên {security_group_id}.")
        return True
        
    except Exception as e:
        # Nếu lỗi là do rule không tồn tại thì không sao, còn lỗi khác thì báo cáo
        if 'InvalidPermission.NotFound' in str(e):
            logger.info(f"Rule mở port 22 không còn tồn tại trên {security_group_id} nữa.")
            return True
            
        logger.error(f"❌ LỖI: Không thể tự động khắc phục SG {security_group_id}. Chi tiết: {str(e)}")
        return False