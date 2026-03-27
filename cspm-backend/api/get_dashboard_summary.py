# Trả về điểm số bảo mật (Security Score), tổng số lỗi
import json
from boto3.dynamodb.conditions import Key
from core.config import DYNAMODB_TABLE, logger
from core.aws_connection import get_boto3_resource

# Khởi tạo kết nối DB ở Global Scope (giúp Lambda chạy nhanh hơn ở các lần gọi sau)
try:
    dynamodb = get_boto3_resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
except Exception as e:
    logger.error(f"Lỗi kết nối DB trong API: {e}")

def lambda_handler(event, context):
    """
    Điểm vào (Entry point) khi API Gateway gọi hàm này.
    """
    logger.info("Đang xử lý yêu cầu lấy dữ liệu thống kê Dashboard...")
    
    try:
        # Dùng lệnh scan() để lấy toàn bộ dữ liệu trong bảng.
        # (Lưu ý: Trong thực tế với hàng triệu record, người ta sẽ dùng query() kết hợp index, 
        # nhưng với đồ án quy mô nhỏ, scan() là hoàn toàn phù hợp và dễ triển khai).
        response = table.scan()
        items = response.get('Items', [])
        
        # Biến đếm thống kê
        total_scanned = len(items)
        failed_count = 0
        passed_count = 0
        
        for item in items:
            if item.get('status') == 'FAIL':
                failed_count += 1
            else:
                passed_count += 1
                
        # Tính điểm bảo mật (Tránh lỗi chia cho 0 nếu DB đang trống)
        security_score = 0
        if total_scanned > 0:
            security_score = round((passed_count / total_scanned) * 100)
            
        # Đóng gói dữ liệu trả về cho Frontend
        response_body = {
            "summary": {
                "security_score": security_score,
                "total_resources_scanned": total_scanned,
                "passed": passed_count,
                "failed": failed_count
            }
        }
        
        return {
            'statusCode': 200,
            # BẮT BUỘC CÓ HEADERS NÀY ĐỂ REACT GỌI ĐƯỢC API MÀ KHÔNG BỊ LỖI CORS
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        logger.error(f"Lỗi API get_dashboard_summary: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"message": "Lỗi máy chủ nội bộ", "error": str(e)})
        }