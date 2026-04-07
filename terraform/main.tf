# 1. CẤU HÌNH NHÀ CUNG CẤP AWS
provider "aws" {
  region = "us-east-1"
}

# 2. TẠO KÉT SẮT DYNAMODB (Nơi chứa danh sách lỗi)
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

# 3. TẠO THẺ NHÂN VIÊN (IAM ROLE & POLICY CHO LAMBDA)
# Cho phép Lambda được phép chạy
resource "aws_iam_role" "lambda_exec_role" {
  name = "cspm_lambda_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Cấp quyền: Ghi log, Đọc/Ghi DynamoDB và Quét cấu hình AWS (SecurityAudit)
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
  policy_arn = "arn:aws:iam::aws:policy/SecurityAudit" # Quyền này cho phép Boto3 quét S3, EC2, IAM...
}

# 4. TẠO ANH BẢO VỆ LAMBDA VÀ ĐƯA CODE (.ZIP) LÊN MÂY
resource "aws_lambda_function" "cspm_scanner" {
  function_name = "cspm-scanner-bot"
  role          = aws_iam_role.lambda_exec_role.arn
  
  # Đường dẫn trỏ tới file zip bạn vừa tạo ở thư mục bên cạnh
  filename      = "../cspm-backend/cspm_backend_payload.zip"

  # BỔ SUNG DÒNG NÀY VÀO ĐỂ TERRAFORM BIẾT CODE ĐÃ THAY ĐỔI
  source_code_hash = filebase64sha256("../cspm-backend/cspm_backend_payload.zip")
  
  # Chỉ định hàm Đội trưởng (orchestrator.py -> hàm lambda_handler)
  handler       = "scanners.orchestrator.lambda_handler"
  runtime       = "python3.10"
  timeout       = 300 # Cho phép chạy tối đa 5 phút vì đi quét nhiều dịch vụ sẽ tốn thời gian

  # Truyền tên bảng DynamoDB và đường dẫn SNS vào cho Python đọc
  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.cspm_findings.name
      SNS_TOPIC_ARN  = aws_sns_topic.cspm_alerts.arn
      SNS_ENABLED    = "true"
    }
  }
}

# 5. LẮP ĐỒNG HỒ BÁO THỨC (EVENTBRIDGE) - Cứ 1 tiếng chạy 1 lần
resource "aws_cloudwatch_event_rule" "every_hour" {
  name                = "cspm-hourly-scan"
  description         = "Kich hoat CSPM Scanner moi gio"
  schedule_expression = "rate(48 hours)"
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

# 5b. LAMBDA TRIGGER SCAN (được gọi từ nút Scan Now trên Frontend)
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

# =========================================================================
# PHẦN 2: XÂY DỰNG API GATEWAY (CẦU NỐI CHO FRONTEND)
# =========================================================================

# 1. Tạo cái "Cửa chính" (API Gateway - HTTP API)
resource "aws_apigatewayv2_api" "cspm_api" {
  name          = "cspm-http-api"
  protocol_type = "HTTP"
  
  # Quan trọng: Cho phép Frontend (CORS) được phép gọi API này
  cors_configuration {
    allow_origins = ["*"] # Mở cho tất cả web gọi vào (Khi làm thật thì nên điền link web của bạn vào đây)
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["content-type"]
  }
}

# 2. Tạo một anh "Lễ tân" (Lambda thứ 2) chuyên đi lấy dữ liệu từ DB trả cho Web
resource "aws_lambda_function" "cspm_api_handler" {
  function_name = "cspm-api-handler"
  role          = aws_iam_role.lambda_exec_role.arn # Dùng chung thẻ nhân viên với anh bảo vệ ở trên
  filename      = "../cspm-backend/cspm_backend_payload.zip" # Vẫn dùng chung cục code đó

  # BỔ SUNG DÒNG NÀY VÀO LUÔN
  source_code_hash = filebase64sha256("../cspm-backend/cspm_backend_payload.zip")
  
  # CHÚ Ý: Chỗ này trỏ tới cái hàm GET dữ liệu của bạn trong thư mục api/
  handler       = "api.get_inventory.lambda_handler"
  runtime       = "python3.10"

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.cspm_findings.name
    }
  }
}

# 3. Mở một cái "Quầy số 1" (Route) trên Cửa chính
resource "aws_apigatewayv2_route" "get_findings_route" {
  api_id    = aws_apigatewayv2_api.cspm_api.id
  route_key = "GET /api/findings" # Đường dẫn URL
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# 2. MỞ THÊM CỬA CHO SUMMARY (MỚI)
resource "aws_apigatewayv2_route" "get_summary_route" {
  api_id    = aws_apigatewayv2_api.cspm_api.id
  route_key = "GET /api/dashboard-summary"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# 2b. LAMBDA REMEDIATE (xử lý nút Remediate trên Frontend)
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

# 3. MỞ THÊM CỬA CHO NÚT SỬA LỖI (MỚI)
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

# 4. ROUTE CHO NÚT SCAN NOW
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

# 4. Nối "Quầy số 1" với anh "Lễ tân" Lambda
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.cspm_api.id
  integration_type = "AWS_PROXY"

  integration_uri        = aws_lambda_function.cspm_api_handler.invoke_arn
  payload_format_version = "2.0"
}

# 5. Cấp quyền cho Cửa chính được phép gọi anh Lễ tân
resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cspm_api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.cspm_api.execution_arn}/*/*"
}

# 6. Mở cửa đón khách (Deploy API)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.cspm_api.id
  name        = "$default"
  auto_deploy = true
}

# 7. IN RA MÀN HÌNH ĐƯỜNG LINK API ĐỂ LÁT NỮA GẮN VÀO FRONTEND REACT
# In ra các đường link để gắn vào code React
output "api_urls" {
  value = {
    get_findings      = "${aws_apigatewayv2_api.cspm_api.api_endpoint}/api/findings"
    dashboard_summary = "${aws_apigatewayv2_api.cspm_api.api_endpoint}/api/dashboard-summary"
    remediate         = "${aws_apigatewayv2_api.cspm_api.api_endpoint}/api/findings/{id}/remediate"
  }
}

# =========================================================================
# PHẦN 3: XÂY DỰNG HỆ THỐNG CẢNH BÁO (AMAZON SNS)
# =========================================================================

# 0. Tạo KMS Key để mã hóa SNS Topic
resource "aws_kms_key" "sns_cmk" {
  description             = "CMK for CSPM SNS Topic encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

# 1. Tạo Kênh thông báo (SNS Topic)
resource "aws_sns_topic" "cspm_alerts" {
  name              = "cspm-security-alerts-topic"
  kms_master_key_id = aws_kms_key.sns_cmk.arn
}

# 2. Đăng ký Email nhận cảnh báo
resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.cspm_alerts.arn
  protocol  = "email"
  # Hãy thay đổi email dưới đây thành email thật của bạn
  endpoint  = "nguyentanloc13102005@gmail.com" 
}

# 3. Tạo quyền (Policy) cho phép gửi tin nhắn vào SNS VÀ DÙNG KHÓA KMS
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
        # BẮT BUỘC PHẢI CÓ DÒNG NÀY THÌ MỚI GỬI ĐƯỢC MAIL KHI ĐÃ BẬT KMS
        Action = [
          "kms:GenerateDataKey*",
          "kms:Decrypt"
        ]
        Effect   = "Allow"
        Resource = aws_kms_key.sns_cmk.arn
      }
    ]
  })
}

# 4. Gắn quyền SNS này vào Thẻ nhân viên (Role) của Lambda hiện tại
resource "aws_iam_role_policy_attachment" "lambda_sns_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_sns_publish.arn
}