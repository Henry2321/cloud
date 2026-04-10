import json
from core.config import logger
from core.aws_connection import get_boto3_client

POLICY_NAME = 'CSPM_ForceMFA'

FORCE_MFA_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyAllExceptMFASetup",
            "Effect": "Deny",
            "NotAction": [
                "iam:CreateVirtualMFADevice",
                "iam:EnableMFADevice",
                "iam:GetUser",
                "iam:ListMFADevices",
                "iam:ListVirtualMFADevices",
                "iam:ResyncMFADevice",
                "sts:GetSessionToken"
            ],
            "Resource": "*",
            "Condition": {
                "BoolIfExists": {
                    "aws:MultiFactorAuthPresent": "false"
                }
            }
        }
    ]
}


def enforce_mfa_policy(user_name):
    """Attach inline policy buộc user phải bật MFA mới dùng được AWS."""
    logger.info(f"Đang enforce MFA policy cho IAM user: {user_name}")
    try:
        iam = get_boto3_client('iam')
        iam.put_user_policy(
            UserName=user_name,
            PolicyName=POLICY_NAME,
            PolicyDocument=json.dumps(FORCE_MFA_POLICY)
        )
        logger.info(f"✅ Đã attach policy {POLICY_NAME} cho user {user_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Lỗi enforce MFA cho {user_name}: {e}")
        return False
