import time
from collections import defaultdict

from core.aws_connection import get_boto3_client
from core.config import logger


def get_cloudwatch_log_events(log_group_name, start_time, end_time, filter_pattern=None, limit=100):
    try:
        client = get_boto3_client('logs')
        params = {
            'logGroupName': log_group_name,
            'startTime': start_time,
            'endTime': end_time,
            'limit': limit
        }
        if filter_pattern:
            params['filterPattern'] = filter_pattern

        return client.filter_log_events(**params)
    except Exception as e:
        logger.error(f"Không thể lấy CloudWatch log events cho {log_group_name}: {e}")
        raise


def detect_spam_ips(log_group, threshold=10, window_seconds=60):
    now = int(time.time() * 1000)
    start_time = now - window_seconds * 1000

    response = get_cloudwatch_log_events(
        log_group_name=log_group,
        start_time=start_time,
        end_time=now,
        filter_pattern='IP=',
        limit=1000
    )

    ip_count = defaultdict(int)

    for event in response.get('events', []):
        message = event.get('message', '')
        if 'IP=' in message:
            try:
                ip = message.split('IP=')[1].split()[0]
                ip_count[ip] += 1
            except Exception:
                continue

    spam_ips = [
        {'ip': ip, 'count': count}
        for ip, count in ip_count.items()
        if count > threshold
    ]

    return spam_ips
