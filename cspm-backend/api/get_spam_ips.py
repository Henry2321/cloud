import json
import boto3
import os
from datetime import datetime, timezone
from decimal import Decimal

cloudwatch = boto3.client('logs', region_name='ap-southeast-2')
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

HISTORY_TABLE = os.environ.get('SPAM_HISTORY_TABLE', 'cspm-spam-ip-history')

def detect_spam_ips(log_group_name, threshold=5, window_seconds=60, limit=1000):
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_time = now - (window_seconds * 1000)

    ip_count = {}
    next_token = None
    total_events = 0

    while True:
        params = {
            "logGroupName": log_group_name,
            "startTime": start_time,
            "endTime": now,
            "filterPattern": "Request received IP=",
            "limit": limit
        }

        if next_token:
            params["nextToken"] = next_token

        response = cloudwatch.filter_log_events(**params)
        events = response.get("events", [])
        total_events += len(events)

        for event in events:
            message = event["message"]
            if "IP=" in message:
                ip = message.split("IP=")[-1].strip()
                ip_count[ip] = ip_count.get(ip, 0) + 1

        next_token = response.get("nextToken")
        if not next_token:
            break

    spam_ips = [
        {"ip": ip, "count": count}
        for ip, count in ip_count.items()
        if count >= threshold
    ]

    return {
        "eventCount": total_events,
        "spamIps": spam_ips,
    }

def save_snapshot(spam_ips, window_from, window_to):
    """Chỉ lưu khi có spam, dùng window_from+window_to làm key"""
    if not spam_ips:
        return

    table = dynamodb.Table(HISTORY_TABLE)
    table.put_item(Item={
        "id":          f"{window_from}_{window_to}",
        "window_from": window_from,
        "window_to":   window_to,
        "spam_ips":    spam_ips,
        "saved_at":    datetime.now(timezone.utc).isoformat()
    })

def load_history(limit=50):
    """Lấy toàn bộ lịch sử, sắp xếp mới nhất lên đầu"""
    table = dynamodb.Table(HISTORY_TABLE)
    items = table.scan().get('Items', [])
    items.sort(key=lambda x: x.get('window_to', ''), reverse=True)
    return items[:limit]

def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj
    
def lambda_handler(event, context):
    # Lấy IP người gọi
    try:
        caller_ip = event["requestContext"]["http"]["sourceIp"]
    except KeyError:
        try:
            caller_ip = event["requestContext"]["identity"]["sourceIp"]
        except KeyError:
            caller_ip = event.get("sourceIp", "127.0.0.1")

    print(f"Request received IP={caller_ip}")

    # Tính khoảng thời gian scan
    now = datetime.now(timezone.utc)
    window_seconds = 60
    window_to   = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    window_from = datetime.fromtimestamp(
        now.timestamp() - window_seconds, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    log_group = '/aws/lambda/cspm-spam-ip-handler'
    threshold = 5

    try:
        # 1. Scan CloudWatch
        result = detect_spam_ips(log_group, threshold, window_seconds)

        # 2. Lưu snapshot nếu có spam
        save_snapshot(result["spamIps"], window_from, window_to)

        history = convert_decimal(load_history())
        current = convert_decimal({
            "window_from": window_from,
            "window_to":   window_to,
            "eventCount":  result["eventCount"],
            "spamIps":     result["spamIps"]
        })
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache"
            },
            "body": json.dumps({
                "current": current,
                "history": history
            })
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Lỗi khi truy vấn CloudWatch", "error": str(e)})
        }