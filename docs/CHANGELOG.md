# Changelog

All notable changes to the **AWS Cost Intelligence** (`cloud-cost-intelligence`) platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-09-17

### Added & Fixed
- **Granular Multi-Tenant RBAC Enforcement**:
  - Enforced `RequirePermission` dependency guards across all sensitive backend routes (`PERM_AWS_CREATE` on AWS account connect, `PERM_ALERTS_CREATE` on alert rules creation, `PERM_INTEGRATIONS_MANAGE` on notification channel creation, `PERM_OPTIMIZATION_MANAGE` on live deep scanning, and `PERM_COSTS_EXPORT` on cost CSV export and sync).
  - Granted `PERM_MEMBERS_UPDATE` and `PERM_MEMBERS_INVITE` permissions to `FINOPS_MANAGER` (Manager) role, enabling managers to manage team member roles within their hierarchy boundary while enforcing role escalation protections.
- **User Deletion & FK Integrity Safety**:
  - Added safe cleanup of sent invitations (`OrganizationInvitation`), `PasswordResetToken`, and `EmailVerificationToken` records before user deletion to eliminate database foreign key constraint violation crashes.
- **Real-Time Active Organization Role Display**:
  - Updated top-right header user badge (`Header.tsx`) and Settings profile view (`Settings.tsx`) to display `activeOrg.role || user.role`, dynamically reflecting active tenant roles.
  - Enhanced `AuthContext.tsx` `refetchOrganizations()` to immediately refresh active organization role state across all pages without requiring a page reload.
  - Added interactive role selector `<select>` dropdown in `AdminUsers.tsx` for `OWNER`, `ADMIN`, `FINOPS_MANAGER` (Manager), and Platform Superadmin roles.

## [1.0.0] - 2026-09-12

### Added
- **Core Platform Architecture**:
  - FastAPI RESTful API with structured `/api/v1/` envelope pattern.
  - PostgreSQL schema with `NUMERIC(18, 4)` precision for strict monetary fidelity.
  - Pluggable Cloud Provider Abstraction (`CloudProvider` base class).
  - AWS Cost Explorer integration adapter supporting dimension queries (SERVICE, LINKED_ACCOUNT, REGION, USAGE_TYPE, TAG).
  - Deterministic Mock AWS Provider with realistic FinOps spending data for Demo Mode.
- **FinOps Dashboard**:
  - Today's cost, Yesterday's cost, and Day Before Yesterday's cost metrics with absolute and percentage variance indicators.
  - Multi-type chart visualizations: Daily Spending Line Chart, Weekly/Monthly Bar Chart, Service Donut Chart, and Spend Scatter Plot.
  - Centralized, stable color registry for AWS services across all renders.
  - Cost concentration views across AWS Services, Accounts, and Regions.
  - Tag coverage quality metrics and untagged spend breakdown.
- **Interactive Cost Exploration**:
  - Searchable, filterable, sortable, paginated Cost Records table.
  - Streaming CSV export matching active filter criteria.
- **Cost Optimization Engine**:
  - 11 modular optimization rules:
    - EC2 idle instances (low CPU utilization)
    - EC2 rightsizing (oversized instances)
    - Unattached EBS volumes
    - Over-provisioned RDS database instances
    - S3 lifecycle & Intelligent-Tiering opportunities
    - NAT Gateway data processing & idle minimization
    - CloudWatch log retention optimization
    - Orphaned snapshots (>90 days old)
    - Tagging compliance & allocation gap identification
    - Compute & EC2 Savings Plans recommendations
    - Reserved Instances coverage recommendations
  - Standardized FinOps recommendation model with Confidence (`Observed`, `Estimated`, `Potential`) and Status (`Requires validation`, `Insufficient data`).
- **Anomaly Detection & Budgets**:
  - Daily cost variance threshold and historical baseline anomaly detection.
  - AWS Budgets tracking with health statuses (`Healthy`, `Warning`, `Critical`, `Exceeded`) and month-end forecasting.
- **Multi-Format Reporting**:
  - CSV, JSON, and executive-styled print-friendly HTML report generation.
  - Local report storage in `backend/reports/` with automatic 90-day retention cleanup.
- **Multi-Channel Notifications**:
  - Common `NotificationProvider` abstraction with health checking and configuration validation.
  - Slack Block Kit webhook integration.
  - Google Chat Card webhook integration.
  - Microsoft Teams Adaptive Card webhook integration.
  - Email (SMTP) notification dispatcher with CSV/HTML report attachments.
- **Security & Governance**:
  - JWT authentication with secure refresh token cycle and role-based access control (`ADMIN`, `USER`).
  - Read-only AWS IAM role architecture using STS `AssumeRole` and `ExternalId`.
  - Structured audit logging for all authentication, report, and integration actions.
  - Masking of sensitive credentials across all API outputs and logs.

