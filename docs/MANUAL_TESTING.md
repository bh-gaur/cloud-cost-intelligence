# Complete Manual Testing Matrix & QA Verification Guide

This document defines the comprehensive 27-point manual QA testing suite for the AWS Cost Intelligence & Multi-Tenant FinOps Platform.

---

## 📋 QA Test Matrix Summary

| Test ID | Test Scenario Name | Primary Module | Priority | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | User Registration & Workspace Creation | Auth & Multi-Tenancy | High | `PASSED` |
| **TC-02** | User Login & JWT Token Issuance | Authentication | Critical | `PASSED` |
| **TC-03** | User Logout & Token Invalidation | Authentication | High | `PASSED` |
| **TC-04** | Forgot Password & Token Reset Flow | Auth & Security | High | `PASSED` |
| **TC-05** | Organization Creation | Multi-Tenancy | High | `PASSED` |
| **TC-06** | Organization Switching | Multi-Tenancy | Critical | `PASSED` |
| **TC-07** | Organization Member Invitation | RBAC & Admin | High | `PASSED` |
| **TC-08** | Role Promotion & Last-Owner Protection | RBAC & Security | Critical | `PASSED` |
| **TC-09** | AWS Account STS Connection Test | AWS Integration | High | `PASSED` |
| **TC-10** | Incremental AWS Cost Synchronization | AWS & Cost Engine | Critical | `PASSED` |
| **TC-11** | Executive Dashboard KPIs & Burn Rate | Dashboard | High | `PASSED` |
| **TC-12** | Multi-Dimensional Cost Filtering | Cost Exploration | High | `PASSED` |
| **TC-13** | Streaming CSV Spend Export | Reporting | High | `PASSED` |
| **TC-14** | HTML Scorecard Report Generation | Reporting | High | `PASSED` |
| **TC-15** | Report Preview & IDOR Protection | Security & Reports | Critical | `PASSED` |
| **TC-16** | Email Report Dispatch | Notifications | Medium | `PASSED` |
| **TC-17** | Slack Webhook Alert Dispatch | Notifications | Medium | `PASSED` |
| **TC-18** | Google Chat Webhook Alert Dispatch | Notifications | Medium | `PASSED` |
| **TC-19** | Microsoft Teams Adaptive Card Alert | Notifications | Medium | `PASSED` |
| **TC-20** | FinOps Optimization Rules Execution | Optimization Engine | High | `PASSED` |
| **TC-21** | Anomaly Spike Threshold Alerting | Alerting | High | `PASSED` |
| **TC-22** | AWS Budget Consumption Tracking | Budgets | Medium | `PASSED` |
| **TC-23** | Mobile Viewport Layout & Drawer | Frontend UX | Medium | `PASSED` |
| **TC-24** | Dark/Light Theme Switching | Frontend UX | Medium | `PASSED` |
| **TC-25** | Invalid Route 444 / Graceful Errors | Error Resilience | High | `PASSED` |
| **TC-26** | Unauthorized API Access Interception | Security | Critical | `PASSED` |
| **TC-27** | Cross-Tenant IDOR Data Access Denial | Multi-Tenancy | Critical | `PASSED` |

---

## 🧪 Detailed Test Specifications

### TC-01: User Registration & Workspace Creation
- **Preconditions**: Unauthenticated user on `/register`.
- **Steps**:
  1. Navigate to `/register`.
  2. Enter Email `newadmin@corp.local`, Password `SecurePass123!@#`, Name `New Admin`, Org Name `Acme Cloud Corp`.
  3. Submit form.
- **Expected Result**: User and organization are created atomically. User is assigned `OWNER` role for `Acme Cloud Corp`.
- **Actual Result**: User created, token issued, redirected to dashboard.
- **Status**: `PASSED`

---

### TC-02: User Login & JWT Token Issuance
- **Preconditions**: User account exists.
- **Steps**:
  1. Navigate to `/login`.
  2. Enter valid credentials (`admin@cloudcost.local` / `Admin123!@#`).
  3. Submit form.
- **Expected Result**: Server returns 200 OK with signed JWT token. User context is populated in app state.
- **Actual Result**: Successfully authenticated and redirected to `/dashboard`.
- **Status**: `PASSED`

---

### TC-03: User Logout & Token Invalidation
- **Preconditions**: User is logged in.
- **Steps**:
  1. Click User Profile in Sidebar/Header.
  2. Click **Sign Out**.
- **Expected Result**: JWT token is cleared from `localStorage`. User is redirected to `/login`.
- **Actual Result**: Session state purged; protected routes redirect to login.
- **Status**: `PASSED`

---

### TC-04: Forgot Password & Token Reset Flow
- **Preconditions**: User registered.
- **Steps**:
  1. Navigate to `/login` and click **Forgot Password**.
  2. Enter user email.
  3. Verify generic success message is returned (preventing account enumeration).
- **Expected Result**: Server returns HTTP 200 with standard response regardless of email existence.
- **Actual Result**: Enumeration protection verified.
- **Status**: `PASSED`

---

### TC-05: Organization Creation
- **Preconditions**: Authenticated user.
- **Steps**:
  1. Navigate to **Admin Settings -> Organizations**.
  2. Click **Create Organization**, enter `Beta Labs`.
- **Expected Result**: Organization created; user added as `OWNER`.
- **Actual Result**: Organization created with unique UUID.
- **Status**: `PASSED`

---

### TC-06: Organization Switching
- **Preconditions**: User belongs to multiple organizations.
- **Steps**:
  1. Select `Beta Labs` from top header Organization dropdown.
- **Expected Result**: React Query queries invalidate. Dashboard updates data context strictly to `Beta Labs`.
- **Actual Result**: Header updates; cost data isolated to selected tenant.
- **Status**: `PASSED`

---

### TC-07: Organization Member Invitation & Manager Role Delegation
- **Preconditions**: `OWNER`, `ADMIN`, or `FINOPS_MANAGER` role in active organization.
- **Steps**:
  1. Navigate to **Admin Settings -> Members**.
  2. Invite `analyst@corp.local` with role `ANALYST`.
- **Expected Result**: Member invitation created. Email dispatch initiated with token link.
- **Actual Result**: Invitation created successfully.
- **Status**: `PASSED`

---

### TC-08: Member Role Update & Real-Time Header Sync
- **Preconditions**: User signed in with `ADMIN` or `FINOPS_MANAGER` role.
- **Steps**:
  1. Navigate to **Admin Settings -> Members**.
  2. Locate an active member row and select new role `FINOPS_MANAGER` from the role dropdown selector.
- **Expected Result**: Role updated in backend via `PATCH`. Top-right header badge and Settings profile view immediately refresh role display to `FINOPS_MANAGER`. Role escalation rules prevent manager from elevating anyone to `ADMIN` or `OWNER`.
- **Actual Result**: Role updated dynamically across all UI components.
- **Status**: `PASSED`

---

### TC-09: AWS Account STS Connection Test
- **Preconditions**: IAM Role configured in target AWS account.
- **Steps**:
  1. Navigate to **Integrations -> AWS Accounts**.
  2. Enter Role ARN `arn:aws:iam::123456789012:role/FinOpsRole` and External ID.
  3. Click **Test AWS Connection**.
- **Expected Result**: STS AssumeRole identity and Cost Explorer permissions are verified.
- **Actual Result**: Connection test returns status and masked account ID.
- **Status**: `PASSED`

---

### TC-10: Incremental AWS Cost Synchronization
- **Preconditions**: AWS Account connected or Mock Provider active.
- **Steps**:
  1. Click **Fetch Live Cost** button in header.
- **Expected Result**: Triggers `POST /api/v1/costs/sync?days=7`. Fetches incremental costs; updates local database.
- **Actual Result**: Synchronized successfully; UI refreshed.
- **Status**: `PASSED`

---

### TC-11: Executive Dashboard KPIs & Burn Rate
- **Preconditions**: Cost records present in DB.
- **Steps**:
  1. View `/dashboard`.
- **Expected Result**: Displays MTD Spend, Projected Month-End Spend, Potential Monthly Savings, Anomaly count, and Top Cost Driver.
- **Actual Result**: All KPIs computed with 100% Decimal precision.
- **Status**: `PASSED`

---

### TC-12: Multi-Dimensional Cost Filtering
- **Preconditions**: Cost records in DB.
- **Steps**:
  1. Navigate to `/costs`.
  2. Filter by Account `Production`, Service `Amazon EC2`, Region `us-east-1`.
- **Expected Result**: Table updates dynamically showing filtered rows and summary total.
- **Actual Result**: Filters applied; pagination accurate.
- **Status**: `PASSED`

---

### TC-13: Streaming CSV Spend Export
- **Preconditions**: Filtered cost view.
- **Steps**:
  1. Click **Export CSV** button on `/costs`.
- **Expected Result**: Streams CSV file `aws-costs-export-YYYY-MM-DD.csv` without memory bloat.
- **Actual Result**: File downloads cleanly with full column layout.
- **Status**: `PASSED`

---

### TC-14: HTML Scorecard Report Generation
- **Preconditions**: Authenticated user.
- **Steps**:
  1. Navigate to `/reports`.
  2. Click **Generate Report**, select format `HTML`, date range `30d`.
- **Expected Result**: Report generated and stored under tenant directory.
- **Actual Result**: Report status set to `COMPLETED`.
- **Status**: `PASSED`

---

### TC-15: Report Preview & IDOR Protection
- **Preconditions**: Report generated in Tenant A. User logged into Tenant B.
- **Steps**:
  1. Tenant B user attempts to access `/api/v1/reports/{tenant_a_report_id}/download`.
- **Expected Result**: Server returns `404 Not Found` or `403 Forbidden`.
- **Actual Result**: Cross-tenant IDOR access strictly blocked.
- **Status**: `PASSED`

---

### TC-16: Email Report Dispatch
- **Preconditions**: SMTP environment variables configured.
- **Steps**:
  1. Trigger report email dispatch to recipient.
- **Expected Result**: Formats HTML summary and attaches report file via SMTP.
- **Actual Result**: Dispatches email; logs status.
- **Status**: `PASSED`

---

### TC-17: Slack Webhook Alert Dispatch
- **Preconditions**: `SLACK_WEBHOOK_URL` configured.
- **Steps**:
  1. Trigger test alert dispatch.
- **Expected Result**: Posts formatted Block Kit JSON payload to Slack webhook.
- **Actual Result**: Successfully dispatched.
- **Status**: `PASSED`

---

### TC-18: Google Chat Webhook Alert Dispatch
- **Preconditions**: `GOOGLE_CHAT_WEBHOOK_URL` configured.
- **Steps**:
  1. Trigger test alert dispatch.
- **Expected Result**: Posts Card v2 payload to Google Chat space.
- **Actual Result**: Successfully dispatched.
- **Status**: `PASSED`

---

### TC-19: Microsoft Teams Adaptive Card Alert
- **Preconditions**: `TEAMS_WEBHOOK_URL` configured.
- **Steps**:
  1. Trigger test alert dispatch.
- **Expected Result**: Posts Adaptive Card v1.4 payload to Teams channel.
- **Actual Result**: Successfully dispatched.
- **Status**: `PASSED`

---

### TC-20: FinOps Optimization Rules Execution
- **Preconditions**: Cost records in DB.
- **Steps**:
  1. Navigate to `/optimization`.
  2. Click **Run FinOps Analysis**.
- **Expected Result**: Evaluates 11+ rules (EBS, EC2, RDS, S3, Idle, Tags). Generates recommendations with confidence scores.
- **Actual Result**: Recommendations listed with priority tags.
- **Status**: `PASSED`

---

### TC-21: Anomaly Spike Threshold Alerting
- **Preconditions**: Anomaly detector active.
- **Steps**:
  1. Run anomaly check against historical spend data.
- **Expected Result**: Detects daily spend increases > 3.0$\sigma$ or > $1,500 threshold.
- **Actual Result**: Alerts generated with severity badges (`CRITICAL`, `WARNING`).
- **Status**: `PASSED`

---

### TC-22: AWS Budget Consumption Tracking
- **Preconditions**: Budget records seeded.
- **Steps**:
  1. View `/dashboard` Budget widget or `/alerts`.
- **Expected Result**: Shows percentage consumed vs. monthly threshold.
- **Actual Result**: Accurately displays budget status.
- **Status**: `PASSED`

---

### TC-23: Mobile Viewport Layout & Drawer
- **Preconditions**: Viewport width set to 375px (iPhone).
- **Steps**:
  1. Open app on mobile browser.
- **Expected Result**: Sidebar collapses into hamburger drawer; tables horizontally scroll.
- **Actual Result**: Layout responsive without visual overflow.
- **Status**: `PASSED`

---

### TC-24: Dark/Light Theme Switching
- **Preconditions**: Any page in app.
- **Steps**:
  1. Click **Sun/Moon** Theme Toggle icon.
- **Expected Result**: Toggles `.dark` class on root HTML element; updates colors instantly.
- **Actual Result**: Transitions cleanly across all components.
- **Status**: `PASSED`

---

### TC-25: Invalid Route 404 / Graceful Errors
- **Preconditions**: Authenticated user.
- **Steps**:
  1. Navigate to `/non-existent-page`.
- **Expected Result**: Renders 404 Not Found page with return to dashboard CTA.
- **Actual Result**: Graceful error UI displayed.
- **Status**: `PASSED`

---

### TC-26: Unauthorized API Access Interception
- **Preconditions**: Expired or missing JWT token.
- **Steps**:
  1. Send request to `/api/v1/costs` without Authorization header.
- **Expected Result**: API returns `401 Unauthorized`.
- **Actual Result**: Request intercepted and rejected.
- **Status**: `PASSED`

---

### TC-27: Cross-Tenant IDOR Data Access Denial
- **Preconditions**: User belongs to Org A.
- **Steps**:
  1. User passes `X-Tenant-ID: org_b` header in API request.
- **Expected Result**: `TenantContext` middleware verifies user membership in Org B and rejects request with `403 Forbidden`.
- **Actual Result**: Strict tenant isolation enforced.
- **Status**: `PASSED`
