# Troubleshooting & Diagnostic Guide

## Common Issues & Solutions

### 1. "AccessDeniedException: User is not authorized to perform: ce:GetCostAndUsage"
- **Cause**: The IAM user or assumed role does not have Cost Explorer permissions enabled.
- **Resolution**:
  1. Ensure Cost Explorer is enabled in the AWS Management Console under Billing > Cost Explorer.
  2. Verify that the IAM policy includes `ce:GetCostAndUsage` on `*`.
  3. Note: In new AWS accounts, Cost Explorer can take up to 24 hours to initialize after activation.

### 2. "Cost Explorer data is not reflecting the last few hours of activity"
- **Cause**: By AWS architectural design, AWS Cost Explorer data updates 3 times per day (roughly every 8–12 hours). It does not provide sub-second real-time streaming data.
- **Resolution**:
  - The UI accurately indicates "Data Freshness" and the timestamp of the last synchronization.
  - To view instant resource creation events, consult CloudTrail or CloudWatch metrics.

### 3. "Database connection refused (PostgreSQL)"
- **Cause**: PostgreSQL service is down or database credentials in `.env` are mismatched.
- **Resolution**:
  - Check Docker service status: `docker compose ps`.
  - For local development without Docker, use SQLite by configuring:
    ```bash
    DATABASE_URL=sqlite:///./cloud_cost.db
    ```

### 4. "Report Download Returns 404"
- **Cause**: The report file may have exceeded `REPORT_RETENTION_DAYS=90` and been purged, or was deleted from the local disk.
- **Resolution**:
  - Generate a fresh report via `POST /api/v1/reports/generate` or the Reports UI page.

