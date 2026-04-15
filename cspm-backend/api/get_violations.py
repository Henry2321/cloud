# Trả về danh sách các tài nguyên vi phạm luật bảo mật
import json
from boto3.dynamodb.conditions import Attr
from core.config import DYNAMODB_TABLE, logger
from core.aws_connection import get_boto3_resource

try:
    dynamodb = get_boto3_resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
except Exception as e:
    logger.error(f"Lỗi kết nối DB trong API: {e}")

def lambda_handler(event, context):
    logger.info("Đang xử lý yêu cầu lấy danh sách tài nguyên vi phạm...")
    
    try:
        # Chỉ quét và kéo về những dòng nào có chữ 'status' là 'FAIL'
        response = table.scan(
            FilterExpression=Attr('status').eq('FAIL')
        )
        violations = response.get('Items', [])
        
        # Sắp xếp lỗi theo thời gian (mới nhất lên đầu). 
        # Vì timestamp lưu dạng chuỗi ISO (VD: 2026-03-25T10:00:00), ta có thể sort trực tiếp chuỗi.
        sorted_violations = sorted(violations, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps({
                "violation_count": len(sorted_violations),
                "findings": sorted_violations   # ĐÃ SỬA TÊN Ở ĐÂY
            }, default=str)                     # ĐÃ THÊM ÉP KIỂU STRING Ở ĐÂY
        }
        
    except Exception as e:
        logger.error(f"Lỗi API get_violations: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"message": "Lỗi máy chủ nội bộ", "error": str(e)})
        }