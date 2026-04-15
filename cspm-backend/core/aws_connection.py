# Khởi tạo session Boto3 an toàn để gọi các dịch vụ AWS
import boto3
from core.config import REGION, logger

def get_boto3_client(service_name):
    """
    Khởi tạo và trả về một Boto3 client an toàn (dùng cho các lệnh gọi API như EC2, S3, IAM)
    """
    try:
        client = boto3.client(service_name, region_name=REGION)
        return client
    except Exception as e:
        logger.error(f"Lỗi cực ngiêm trọng: Không thể khởi tạo AWS Client cho {service_name}. Chi tiết: {e}")
        raise

def get_boto3_resource(service_name):
    """
    Khởi tạo Boto3 resource (Thường dùng riêng cho thao tác với DynamoDB)
    """
    try:
        resource = boto3.resource(service_name, region_name=REGION)
        return resource
    except Exception as e:
        logger.error(f"Lỗi cực ngiêm trọng: Không thể khởi tạo AWS Resource cho {service_name}. Chi tiết: {e}")
        raise