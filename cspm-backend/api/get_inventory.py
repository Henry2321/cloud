import json
from core.config import DYNAMODB_TABLE, logger
from core.aws_connection import get_boto3_resource

# Khởi tạo kết nối DB ở Global Scope (giúp Lambda chạy nhanh hơn)
try:
    dynamodb = get_boto3_resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
except Exception as e:
    logger.error(f"Lỗi kết nối DB trong API: {e}")

def lambda_handler(event, context):
    logger.info("Đang xử lý yêu cầu từ Dashboard...")
    
    # Lấy đường dẫn URL để biết Web đang hỏi cái gì
    path = event.get('rawPath', event.get('path', ''))

    try:
        response = table.scan()
        items = response.get('Items', [])
        
        # --- TRƯỜNG HỢP 1: WEB HỎI SUMMARY (LẤY SỐ LIỆU VẼ BIỂU ĐỒ) ---
        if "dashboard-summary" in path:
            passed = len([i for i in items if i.get('status') == 'PASS'])
            failed = len([i for i in items if i.get('status') == 'FAIL'])
            total = len(items)
            score = round((passed / total * 100)) if total > 0 else 0
            
            result = {
                "summary": {
                    "security_score": score,
                    "passed": passed,
                    "failed": failed,
                    "total_assets": total,
                    "total_resources_scanned": total,
                    "open_findings": failed,
                    "resolved_findings": 0,
                    "last_updated": items[0].get('timestamp') if items else None
                }
            }

        # --- TRƯỜNG HỢP 2: WEB HỎI FINDINGS (LẤY DANH SÁCH BẢNG LỖI) ---
        else:
            findings_list = []
            for item in items:
                findings_list.append({
                    "id": item.get('id', ''),
                    "title": item.get('resource_name', 'Unknown'),
                    "rule_name": item.get('rule_name', 'Security Policy'),
                    "service": item.get('service', 'AWS'),
                    "severity": item.get('severity', 'LOW'),
                    "status": item.get('status', 'PASS'),
                    "time": item.get('timestamp', ''),
                    "action": "Remediate"
                })
            result = {"findings": findings_list}

        # TRẢ VỀ CHO WEB (Cấu hình CORS đầy đủ)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Lỗi: {str(e)}")
        return {
            'statusCode': 500, 
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"error": str(e)})
        }