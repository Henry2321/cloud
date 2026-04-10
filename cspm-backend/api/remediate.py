import json
from core.config import DYNAMODB_TABLE, logger
from core.aws_connection import get_boto3_resource
from remediations.s3_remediator import fix_s3_public_access
from remediations.sg_remediator import remove_open_ssh
from remediations.iam_remediator import enforce_mfa_policy

try:
    dynamodb = get_boto3_resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
except Exception as e:
    logger.error(f"Lỗi kết nối DB: {e}")

def lambda_handler(event, context):
    # Lấy finding id từ URL /api/findings/{id}/remediate
    path_params = event.get('pathParameters') or {}
    path_parts = event.get('rawPath', '').split('/')
    finding_id = path_params.get('id') or (path_parts[3] if len(path_parts) > 3 else None)

    if not finding_id:
        return _response(400, {"message": "Thiếu finding id"})

    try:
        # Tìm finding trong DynamoDB
        result = table.get_item(Key={'id': finding_id})
        finding = result.get('Item')

        if not finding:
            return _response(404, {"message": f"Không tìm thấy finding: {finding_id}"})

        if finding.get('status') == 'PASS':
            return _response(200, {"message": "Finding này đã được khắc phục rồi.", "finding": finding})

        service = finding.get('service', '')
        rule_name = finding.get('rule_name', '')
        resource_name = finding.get('resource_name', '')
        resource_id = finding.get('resource_id', '')

        success = False

        # Gọi đúng remediator theo service + rule
        if service == 'S3' and rule_name == 'S3_Block_Public_Access':
            success = fix_s3_public_access(resource_name)

        elif service == 'EC2' and rule_name == 'EC2_SG_SSH_RDP_OPEN':
            # resource_id dạng arn:aws:ec2:::security-group/sg-xxxxxxxx
            sg_id = resource_id.split('/')[-1] if '/' in resource_id else resource_name
            success = remove_open_ssh(sg_id)

        elif service == 'IAM' and rule_name == 'IAM_User_MFA_Enabled':
            success = enforce_mfa_policy(resource_name)

        else:
            return _response(400, {"message": f"Chưa hỗ trợ tự động remediate cho {service} / {rule_name}"})

        if success:
            # Cập nhật status trong DynamoDB
            table.update_item(
                Key={'id': finding_id},
                UpdateExpression="SET #s = :pass_val",
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':pass_val': 'PASS'}
            )
            logger.info(f"✅ Remediated finding {finding_id} ({service} - {resource_name})")
            return _response(200, {"message": "Khắc phục thành công!", "finding_id": finding_id})
        else:
            return _response(500, {"message": "Khắc phục thất bại, xem CloudWatch log để biết chi tiết."})

    except Exception as e:
        logger.error(f"Lỗi remediate: {e}")
        return _response(500, {"message": str(e)})


def _response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, ensure_ascii=False)
    }
