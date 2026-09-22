# API Reference Specification

All endpoints are versioned under `/api/v1` and return standardized envelopes.

## Response Envelope Format

### Success Response (`200 OK`, `201 Created`)
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": "2026-09-12T09:30:00Z",
    "version": "v1",
    "demo_mode": true
  }
}
```

### Error Response (`400`, `401`, `403`, `404`, `500`)
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date range: start_date must be before end_date.",
    "details": null
  },
  "meta": {
    "timestamp": "2026-09-12T09:30:00Z",
    "version": "v1",
    "demo_mode": true
  }
}
```

---

## Endpoints

### 1. Health & Readiness
- `GET /health`: Overall service health.
- `GET /health/db`: Database connectivity check.
- `GET /health/aws`: Cloud provider connectivity check.

### 2. Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register`: Register a new user (`email`, `password`, `full_name`).
- `POST /api/v1/auth/login`: Authenticate and receive JWT access and refresh tokens.
- `POST /api/v1/auth/refresh`: Refresh expired access token using valid refresh token.
- `GET /api/v1/auth/me`: Retrieve authenticated user profile and roles.
- `POST /api/v1/auth/forgot-password`: Request password reset email.
- `POST /api/v1/auth/reset-password`: Complete password reset with token.

### 3. FinOps Dashboard (`/api/v1/dashboard`)
- `GET /api/v1/dashboard/summary`: Returns Today's cost, Yesterday's cost, Day before yesterday's cost, absolute differences, percentage changes, data freshness timestamp, and active AWS account/region.
- `GET /api/v1/dashboard/kpis`: Total monthly spend, projected month-end spend, potential monthly savings, untagged spend percentage, budget utilization, and active anomalies.
- `GET /api/v1/dashboard/trends?range=30d&type=daily`: Historical spend records formatted for Line, Bar, Donut, and Scatter charts.

### 4. Costs Exploration (`/api/v1/costs`)
- `GET /api/v1/costs`: Paginated and filterable cost records list.
  - Query params: `page`, `page_size`, `start_date`, `end_date`, `account_id`, `service`, `region`, `min_cost`, `max_cost`, `tag_key`, `tag_value`, `sort_by`, `sort_order`.
- `GET /api/v1/costs/export/csv`: Streams a CSV file matching the applied query parameters.

### 5. Services Breakdown (`/api/v1/services`)
- `GET /api/v1/services`: List of all AWS services with spend, percentage of total, previous period spend, variance, and trend direction.
- `GET /api/v1/services/{service_name}`: Detailed service breakdown including usage type distribution, regional spread, and historical cost timeline.

### 6. Accounts & Multi-Account (`/api/v1/accounts`)
- `GET /api/v1/accounts`: Multi-account AWS Organizations summary table.
- `GET /api/v1/accounts/{account_id}`: Account-specific spending trends and active services.

### 7. Regions Breakdown (`/api/v1/regions`)
- `GET /api/v1/regions`: Geographical spend distribution by AWS region (e.g. `us-east-1`, `eu-west-1`).

### 8. Cost Optimization (`/api/v1/optimization`)
- `GET /api/v1/optimization/recommendations`: List of active recommendations with filtering by `service`, `priority` (`HIGH`, `MEDIUM`, `LOW`), and `confidence` (`Observed`, `Estimated`, `Potential`).
- `POST /api/v1/optimization/run`: Manually triggers evaluation of all 11+ optimization rules.
- `GET /api/v1/optimization/summary`: Aggregate potential monthly and annual savings.

### 9. Alerts & Budgets (`/api/v1/alerts`)
- `GET /api/v1/alerts`: Active alerts list and alert rules configuration.
- `POST /api/v1/alerts`: Create a new alert rule (threshold, metric, notification channel).
- `GET /api/v1/alerts/anomalies`: Historical detected anomalies timeline.
- `GET /api/v1/alerts/budgets`: AWS Budgets status, forecasted spend, and threshold consumption.

### 10. Reports Engine (`/api/v1/reports`)
- `GET /api/v1/reports`: List of previously generated reports with format, file size, creation date, and status.
- `POST /api/v1/reports/generate`: Generate a new report (`format`: `csv` | `json` | `html`, `date_range`, `account_id`).
- `GET /api/v1/reports/{id}/download`: Secure streaming download of a generated report.
- `DELETE /api/v1/reports/{id}`: Delete a report and purge its local file.

### 11. Integrations (`/api/v1/integrations` & `/api/v1/aws`)
- `POST /api/v1/aws/test-connection`: Validates AWS IAM credentials, STS identity, and Cost Explorer accessibility. Returns masked account and status.
- `POST /api/v1/notifications/test`: Dispatches a test payload to a configured channel (Slack, Teams, GChat, Email) and returns delivery status.

### 12. Organization & Member Management (`/api/v1/organizations`)
- `GET /api/v1/organizations/me`: List all organizations user belongs to with active roles.
- `POST /api/v1/organizations`: Create new organization and assign caller as `OWNER`.
- `POST /api/v1/organizations/switch`: Switch active tenant context.
- `GET /api/v1/organizations/{org_id}/members`: List organization members.
- `POST /api/v1/organizations/{org_id}/members/invite`: Invite new member by email (Requires `PERM_MEMBERS_INVITE`).
- `PATCH /api/v1/organizations/{org_id}/members/{member_id}`: Update member role or status (Requires `PERM_MEMBERS_UPDATE`; enforces role escalation protection).
- `DELETE /api/v1/organizations/{org_id}/members/{member_id}`: Remove member (Requires `PERM_MEMBERS_REMOVE`; enforces last-owner protection).

### 13. Administration (`/api/v1/admin`)
- `GET /api/v1/admin/users`: User directory management (Admin only).
- `DELETE /api/v1/admin/users/{user_id}`: Permanently delete user and purge associated sessions/invitations.
- `GET /api/v1/admin/audit-logs`: Paginated audit log records for tenant.
- `GET /api/v1/admin/system`: System resource status and disk retention usage.

