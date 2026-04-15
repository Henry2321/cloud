# CloudWatch Logs Support

This backend now includes support for AWS CloudWatch Logs in `server.js`.

## Required dependency

Install the AWS SDK in the backend folder:

```powershell
cd cspm-backend
npm install aws-sdk
```

## New API routes

- `GET /api/cloudwatch/log-groups?prefix=...&limit=50&nextToken=...`
- `GET /api/cloudwatch/log-streams?logGroupName=...&prefix=...&limit=50&nextToken=...`
- `GET /api/cloudwatch/log-events?logGroupName=...&startTime=...&endTime=...&limit=100&nextToken=...`

## Parameters

- `logGroupName`: required for log streams and log events
- `prefix`: optional prefix filter
- `limit`: optional maximum number of items
- `startTime` / `endTime`: either epoch milliseconds or ISO date string

## Notes

- AWS credentials must be available via environment or shared AWS config.
- The backend uses `process.env.AWS_REGION` or defaults to `us-east-1`.
