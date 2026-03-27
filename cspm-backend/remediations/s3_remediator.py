# Code tự động bật Block Public Access cho S3 bị lỗi
from core.config import logger
from core.aws_connection import get_boto3_client

def fix_s3_public_access(bucket_name):
    """
    Hàm tự động bật 'Block All Public Access' cho S3 Bucket.
    """
    logger.info(f"Đang tiến hành tự động khắc phục (Remediate) cho S3 Bucket: {bucket_name}")
    
    try:
        s3_client = get_boto3_client('s3')
        
        # Gọi API của AWS để ép buộc khóa toàn bộ Public Access
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        
        logger.info(f"✅ THÀNH CÔNG: Đã đóng cửa Public Access cho bucket {bucket_name}.")
        return True
        
    except Exception as e:
        logger.error(f"❌ LỖI: Không thể tự động khắc phục S3 {bucket_name}. Chi tiết: {str(e)}")
        return False