# Operations & Maintenance Guide

This document outlines Day-2 operations, monitoring procedures, database maintenance, backup policies, and incident response runbooks for the AWS Cost Intelligence Platform.

---

## 🔁 Scheduled Maintenance & Cron Jobs

The platform relies on the following scheduled background tasks:

| Schedule | Command / Routine | Purpose |
| :--- | :--- | :--- |
| **Daily at 01:00 UTC** | `POST /api/v1/costs/sync?days=7` | Incremental AWS Cost Explorer ingestion |
| **Daily at 02:00 UTC** | `AnomalyDetector.detect_daily_anomalies()` | Statistical spend anomaly analysis & alerts |
| **Daily at 03:00 UTC** | `OptimizationEngine.run_all()` | Refresh FinOps waste recommendations |
| **Monthly on 1st** | `ReportService.generate_monthly_reports()` | Automated Executive Scorecard PDF/CSV generation |

---

## 💾 Database Backup & Recovery Runbook

### 1. SQLite Local Backup (Development / Staging)
```bash
# Live backup using sqlite3 CLI
sqlite3 cloud_cost.db ".backup 'backups/cloud_cost_backup_$(date +%Y%m%d_%H%M%S).db'"
```

### 2. PostgreSQL Production Backup & Restore
```bash
# Database Dump (Compressed)
pg_dump -U finops_user -h db.internal -d cloud_cost_db -F c -b -v -f "backups/cloud_cost_db_$(date +%Y%m%d).dump"

# Database Restore
pg_restore -U finops_user -h db.internal -d cloud_cost_db -v "backups/cloud_cost_db_20260915.dump"
```

---

## 🔒 Secret Rotation Runbook

1. **JWT `SECRET_KEY` Rotation**:
   - Update `SECRET_KEY` in production environment variables.
   - Note: Changing `SECRET_KEY` will invalidate existing user sessions, requiring users to log in again.
2. **AWS External ID / Role ARN Rotation**:
   - Update `role_arn` or `external_id` in AWS IAM Console.
   - Navigate to **Integrations -> AWS Accounts** in the platform UI and update account settings.
   - Click **Test AWS Connection** to verify identity.

---

## 🚨 Incident Response & Troubleshooting

### Issue 1: High AWS Cost Explorer API Spend
- **Symptom**: AWS bill shows increased `ce:GetCostAndUsage` charges.
- **Cause**: Excessive manual sync triggers or un-cached polling.
- **Resolution**: Verify local DB cache is populated. The platform is configured to perform incremental 7-day syncs. Avoid running full 90-day syncs more than once per week.

### Issue 2: Cross-Tenant Data Access Attempt (403 Forbidden)
- **Symptom**: User receives `403 Forbidden` error when switching context.
- **Cause**: User is attempting to access an organization they do not belong to.
- **Resolution**: Check `audit_logs` table for `TENANT_ACCESS_DENIED` events. Verify user's organization memberships in **Admin -> Members**.
