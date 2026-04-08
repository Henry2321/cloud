# 1. CẤU HÌNH NHÀ CUNG CẤP AWS
provider "aws" {
  region = "us-east-1"
}

# =========================================================================
# PHẦN 1: DATABASE & QUYỀN HẠN (IAM)
# =========================================================================

# 2. TẠO KÉT SẮT DYNAMODB
resource "aws_dynamodb_table" "cspm_findings" {
  name           = "cspm-findings-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}

# 3. TẠO THẺ NHÂN VIÊN (ĐÃ FIX TÊN THÀNH V2 ĐỂ ÉP AWS CHẠY, KHÔNG BỊ LỖI ASSUME ROLE)
resource "aws_iam_role" "lambda_exec_role" {
  name = "cspm_lambda_execution_role_v2"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Các quyền cơ bản
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}
resource "aws_iam_role_policy_attachment" "lambda_security_audit" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/SecurityAudit"
}
# Quyền của Phúc: Đọc CloudWatch Logs cho tính năng Spam IP
resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_read" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsReadOnlyAccess"
}

# =========================================================================
# PHẦN 2: CÁC HÀM LAMBDA (ĐỘI QUÂN NHÂN VIÊN)
# =========================================================================

# Lambda 1: Con Bot đi quét
resource "aws_lambda_function" "cspm_scanner" {
  function_name    = "cspm-scanner-bot"
  role             = aws_iam_role.lambda_exec_role.arn
  filename         = "../cspm-backend/cspm_backend_payload.zip"
  source_code_hash = filebase64sha256("../cspm-backend/cspm_backend_payload.zip")
  handler          = "scanners.orchestrator.lambda_handler"
  runtime          = "python3.10"
  timeout          = 300

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.cspm_findings.name
      SNS_TOPIC_ARN  = aws_sns_topic.cspm_alerts.arn
      SNS_ENABLED    = "true"
    }
  }
}

# Lambda 2: Kích hoạt quét từ nút Scan Now
resource "aws_lambda_function" "cspm_scan_trigger" {
  function_name    = "cspm-scan-trigger"
  role             = aws_iam_role.lambda_exec_role.arn
  filename         = "../cspm-backend/cspm_backend_payload.zip"
  source_code_hash = filebase64sha256("../cspm-backend/cspm_backend_payload.zip")
  handler          = "scanners.orchestrator.lambda_handler"
  runtime          = "python3.10"
  timeout          = 300

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.cspm_findings.name
      SNS_TOPIC_ARN  = aws_sns_topic.cspm_alerts.arn
    }
  }
}

# Lambda 3: Lễ tân lấy dữ liệu (Dashboard & Findings)
resource "aws_lambda_function" "cspm_api_handler" {
  function_name    = "cspm-api-handler"
  role             = aws_iam_role.lambda_exec_role.arn
  filename         = "../cspm-backend/cspm_backend_payload.zip"
  source_code_hash = filebase64sha256("../cspm-backend/cspm_backend_payload.zip")
  handler          = "api.get_inventory.lambda_handler"
  runtime          = "python3.10"
  timeout          = 30

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.cspm_findings.name
    }
  }
}

# Lambda 4: Sửa lỗi tự động Remediate
resource "aws_lambda_function" "cspm_remediator" {
  function_name    = "cspm-remediator"
  role             = aws_iam_role.lambda_exec_role.arn
  filename         = "../cspm-backend/cspm_backend_payload.zip"
  source_code_hash = filebase64sha256("../cspm-backend/cspm_backend_payload.zip")
  handler          = "api.remediate.lambda_handler"
  runtime          = "python3.10"
  timeout          = 60

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.cspm_findings.name
    }
  }
}

# Lambda 5: Đọc Spam IPs (Của Phúc)
resource "aws_lambda_function" "cspm_spam_ip_handler" {
  function_name    = "cspm-spam-ip-handler"
  role             = aws_iam_role.lambda_exec_role.arn
  filename         = "../cspm-backend/cspm_backend_payload.zip"
  source_code_hash = filebase64sha256("../cspm-backend/cspm_backend_payload.zip")
  handler          = "api.get_spam_ips.lambda_handler"
  runtime          = "python3.10"
  timeout          = 30
}

# Đồng hồ báo thức (EventBridge)
resource "aws_cloudwatch_event_rule" "every_hour" {
  name                = "cspm-hourly-scan"
  description         = "Kich hoat CSPM Scanner moi gio"
  schedule_expression = "rate(72 hours)"
}
resource "aws_cloudwatch_event_target" "trigger_scanner" {
  rule      = aws_cloudwatch_event_rule.every_hour.name
  target_id = "lambda"
  arn       = aws_lambda_function.cspm_scanner.arn
}
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cspm_scanner.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_hour.arn
}

# =========================================================================
# PHẦN 3: XÂY DỰNG API GATEWAY (CỬA CHÍNH)
# =========================================================================

resource "aws_apigatewayv2_api" "cspm_api" {
  name          = "cspm-http-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["content-type"]
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.cspm_api.id
  name        = "$default"
  auto_deploy = true
}

# 1. Route: Get Findings
resource "aws_apigatewayv2_route" "get_findings_route" {
  api_id    = aws_apigatewayv2_api.cspm_api.id
  route_key = "GET /api/findings"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# 2. Route: Dashboard Summary
resource "aws_apigatewayv2_route" "get_summary_route" {
  api_id    = aws_apigatewayv2_api.cspm_api.id
  route_key = "GET /api/dashboard-summary"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Integration dùng chung
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.cspm_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.cspm_api_handler.invoke_arn
  payload_format_version = "2.0"
}
resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cspm_api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.cspm_api.execution_arn}/*/*"
}

# 3. Route: Scan Now
resource "aws_apigatewayv2_route" "scan_route" {
  api_id    = aws_apigatewayv2_api.cspm_api.id
  route_key = "POST /api/scan"
  target    = "integrations/${aws_apigatewayv2_integration.scan_integration.id}"
}
resource "aws_apigatewayv2_integration" "scan_integration" {
  api_id                 = aws_apigatewayv2_api.cspm_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.cspm_scan_trigger.invoke_arn
  payload_format_version = "2.0"
}
resource "aws_lambda_permission" "api_gw_scan" {
  statement_id  = "AllowExecutionFromAPIGatewayScan"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cspm_scan_trigger.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.cspm_api.execution_arn}/*/*"
}

# 4. Route: Remediate
resource "aws_apigatewayv2_route" "remediate_route" {
  api_id    = aws_apigatewayv2_api.cspm_api.id
  route_key = "POST /api/findings/{id}/remediate"
  target    = "integrations/${aws_apigatewayv2_integration.remediate_integration.id}"
}
resource "aws_apigatewayv2_integration" "remediate_integration" {
  api_id                 = aws_apigatewayv2_api.cspm_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.cspm_remediator.invoke_arn
  payload_format_version = "2.0"
}
resource "aws_lambda_permission" "api_gw_remediate" {
  statement_id  = "AllowExecutionFromAPIGatewayRemediate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cspm_remediator.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.cspm_api.execution_arn}/*/*"
}

# 5. Route: Spam IPs
resource "aws_apigatewayv2_route" "get_spam_ips_route" {
  api_id    = aws_apigatewayv2_api.cspm_api.id
  route_key = "GET /api/cloudwatch/spam-ips"
  target    = "integrations/${aws_apigatewayv2_integration.spam_ip_integration.id}"
}
resource "aws_apigatewayv2_integration" "spam_ip_integration" {
  api_id                 = aws_apigatewayv2_api.cspm_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.cspm_spam_ip_handler.invoke_arn
  payload_format_version = "2.0"
}
resource "aws_lambda_permission" "api_gw_spam_ip" {
  statement_id  = "AllowExecutionFromAPIGatewaySpamIp"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cspm_spam_ip_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.cspm_api.execution_arn}/*/*"
}

# =========================================================================
# PHẦN 4: HỆ THỐNG CẢNH BÁO (AMAZON SNS & KMS)
# =========================================================================

data "aws_caller_identity" "current" {}

resource "aws_kms_key" "sns_cmk" {
  description             = "CMK for CSPM SNS Topic encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "cspm-kms-policy"
    Statement = [
      {
        Sid    = "AllowAccountRoot"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowLambdaExecutionRole"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_exec_role.arn
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_sns_topic" "cspm_alerts" {
  name = "cspm-security-alerts-topic"
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.cspm_alerts.arn
  protocol  = "email"
  endpoint  = "nguyentanloc13102005@gmail.com" 
}

resource "aws_iam_policy" "lambda_sns_publish" {
  name        = "cspm_lambda_sns_publish_policy"
  description = "Cho phep Lambda gui canh bao qua SNS va dung khoa KMS"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "sns:Publish"
        Effect   = "Allow"
        Resource = aws_sns_topic.cspm_alerts.arn
      },
      {
        Action = [
          "kms:GenerateDataKey*",
          "kms:Decrypt",
          "kms:CreateGrant"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sns_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_sns_publish.arn
}

# =========================================================================
# PHẦN 5: IN RA KẾT QUẢ ĐỂ GẮN VÀO FRONTEND
# =========================================================================
output "api_urls" {
  value = {
    get_findings      = "${aws_apigatewayv2_api.cspm_api.api_endpoint}/api/findings"
    dashboard_summary = "${aws_apigatewayv2_api.cspm_api.api_endpoint}/api/dashboard-summary"
    remediate         = "${aws_apigatewayv2_api.cspm_api.api_endpoint}/api/findings/{id}/remediate"
    spam_ips          = "${aws_apigatewayv2_api.cspm_api.api_endpoint}/api/cloudwatch/spam-ips"
  }
}