# deploy-lambda.ps1 - Build va deploy cspm-remediator len AWS Lambda
Set-Location "$PSScriptRoot\cspm-backend"

$ZIP = "cspm_backend_payload.zip"
$BUILD = "build_temp"

Write-Host "=== BUILD & DEPLOY cspm-remediator ===" -ForegroundColor Cyan

# 1. Don dep
if (Test-Path $BUILD) { Remove-Item $BUILD -Recurse -Force }
if (Test-Path $ZIP)   { Remove-Item $ZIP -Force }

# 2. Tao thu muc tam
New-Item -ItemType Directory -Path $BUILD | Out-Null

# 3. Cai thu vien
Write-Host "Cai dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -t $BUILD --quiet

# 4. Copy source
Copy-Item -Recurse api         "$BUILD\api"
Copy-Item -Recurse core        "$BUILD\core"
Copy-Item -Recurse scanners    "$BUILD\scanners"
Copy-Item -Recurse notifications "$BUILD\notifications"
Copy-Item -Recurse remediations  "$BUILD\remediations"

# 5. Nen zip
Write-Host "Nen zip..." -ForegroundColor Yellow
Push-Location $BUILD
python -m zipfile -c "..\$ZIP" .
Pop-Location

# 6. Don dep
Remove-Item $BUILD -Recurse -Force

Write-Host "Da tao $ZIP" -ForegroundColor Green

# 7. Deploy len Lambda
Write-Host "Deploy len AWS Lambda cspm-remediator..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name cspm-remediator `
    --zip-file "fileb://$ZIP" `
    --region us-east-1

Write-Host "=== HOAN TAT ===" -ForegroundColor Green
