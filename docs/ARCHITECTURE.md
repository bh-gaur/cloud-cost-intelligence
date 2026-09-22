# System Architecture Specification

## Overview

The **AWS Cost Intelligence** platform (`cloud-cost-intelligence`) is designed for resilient, scalable, multi-account FinOps monitoring, optimization, reporting, and alerting. It isolates external cloud vendor APIs from consumption layers using a strict **Cloud Provider Abstraction**.

---

## 1. High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Presentation Layer"]
        Browser["React 18 + Vite + Tailwind UI"]
        Mobile["Mobile / Tablet Viewport"]
        ExportCLI["CLI Tool / cURL Consumers"]
    end

    subgraph ApiGateway ["FastAPI Application Boundary (/api/v1)"]
        CorsMdlw["CORS & Secure Headers"]
        RateLmt["Rate Limiter & Audit Interceptor"]
        JwtAuth["JWT Auth / RBAC Guard (Admin/User)"]
        Router["API Subrouters"]
        
        CorsMdlw --> RateLmt --> JwtAuth --> Router
    end

    subgraph ServiceCore ["FinOps Business Logic"]
        CostService["Cost Aggregation Service"]
        OptEngine["Optimization Rule Engine"]
        AnomalyService["Anomaly Detection Service"]
        ReportService["Report Generation Engine"]
        NotifService["Notification Dispatcher"]
        SyncWorker["Incremental Sync Engine"]
    end

    subgraph ProviderAbstraction ["Cloud Provider Layer"]
        BaseProvider["CloudProvider (Interface)"]
        AWSImpl["AWS Provider (Boto3 Adapter)"]
        MockImpl["Mock AWS Provider (Demo Mode)"]
        
        BaseProvider --> AWSImpl
        BaseProvider --> MockImpl
    end

    subgraph ExternalCloud ["AWS Cloud APIs (Read-Only)"]
        CostExplorer["AWS Cost Explorer"]
        Budgets["AWS Budgets"]
        AnomalyAPI["AWS Cost Anomaly Detection"]
        ResourceAPIs["EC2 / RDS / S3 / CloudWatch Metadata"]
    end

    subgraph StorageLayer ["Persistence & File Storage"]
        PostgresDB[(PostgreSQL 16 DB / NUMERIC 18,4)]
        ReportStore[("Local Report Storage (CSV/JSON/HTML)")]
    end

    subgraph Channels ["External Alert Channels"]
        SlackHook["Slack Block Kit"]
        TeamsHook["MS Teams Adaptive Cards"]
        GChatHook["Google Chat Webhook"]
        EmailSMTP["SMTP Mail Server"]
    end

    Browser --> ApiGateway
    Mobile --> ApiGateway
    ExportCLI --> ApiGateway

    Router --> CostService
    Router --> OptEngine
    Router --> AnomalyService
    Router --> ReportService
    Router --> NotifService

    CostService --> BaseProvider
    OptEngine --> BaseProvider
    AnomalyService --> BaseProvider
    SyncWorker --> BaseProvider

    AWSImpl --> CostExplorer
    AWSImpl --> Budgets
    AWSImpl --> AnomalyAPI
    AWSImpl --> ResourceAPIs

    CostService --> PostgresDB
    ReportService --> PostgresDB
    ReportService --> ReportStore
    NotifService --> Channels
```

---

## 2. AWS Data Ingestion & Normalization Flow

```mermaid
sequenceDiagram
    autonumber
    participant Worker as Sync Worker / fetch_costs.py
    participant Adapter as AWS Cost Explorer Adapter
    participant AWS as AWS Cost Explorer API
    participant Normalizer as Cost Normalizer
    participant DB as PostgreSQL Database
    participant Cache as Aggregated Daily Summaries

    Worker->>Adapter: fetch_daily_costs(start_date, end_date, accounts)
    Adapter->>AWS: ce.get_cost_and_usage(GroupBy=[SERVICE, ACCOUNT, REGION])
    AWS-->>Adapter: Raw AWS Cost Explorer JSON Payload
    Adapter->>Normalizer: normalize_dimensions(raw_records)
    Normalizer->>Normalizer: Convert monetary strings to Decimal(18, 4)
    Normalizer->>Normalizer: Deduplicate and assign unique idempotency keys
    Normalizer->>DB: Bulk Upsert CostRecords
    Worker->>Cache: Refresh DailyCostSummary & ServiceCostSummary
    Cache->>DB: Write aggregated rollups
```

---

## 3. Cost Optimization Engine Architecture

The optimization engine evaluates infrastructure metadata against FinOps efficiency rules. Rules return a standardized `Recommendation` object:

```mermaid
flowchart LR
    subgraph Engine ["Optimization Engine"]
        Runner["Rule Runner"]
    end

    subgraph Rules ["Modular FinOps Rules"]
        R1["EC2 Idle Rule"]
        R2["EC2 Rightsizing Rule"]
        R3["EBS Unused Rule"]
        R4["RDS Rightsizing Rule"]
        R5["S3 Storage Tiering Rule"]
        R6["NAT Gateway Optimizer"]
        R7["CloudWatch Retention Rule"]
        R8["Orphaned Snapshot Rule"]
        R9["Tagging Compliance Rule"]
        R10["Savings Plans Analyzer"]
        R11["Reserved Instances Analyzer"]
    end

    subgraph Output ["Standardized FinOps Recommendation"]
        Model["Rule ID<br/>Resource ARN<br/>Service & Region<br/>Current Cost (Decimal)<br/>Estimated Monthly Savings<br/>Estimated Annual Savings<br/>Confidence (Observed/Estimated/Potential)<br/>Status (Requires validation / Insufficient data)<br/>Remediation Steps"]
    end

    Runner --> R1 & R2 & R3 & R4 & R5 & R6 & R7 & R8 & R9 & R10 & R11
    R1 & R2 & R3 & R4 & R5 & R6 & R7 & R8 & R9 & R10 & R11 --> Model
```

---

## 4. Multi-Channel Notification Workflow

```mermaid
flowchart TD
    Trigger["Report Generated / Anomaly Detected / Budget Alert"]
    Dispatcher["Notification Dispatcher"]
    
    Trigger --> Dispatcher

    subgraph Providers ["Notification Provider Implementations"]
        P_Slack["Slack Provider (Block Kit)"]
        P_Teams["Teams Provider (Adaptive Cards)"]
        P_GChat["Google Chat Provider (Cards v2)"]
        P_Email["Email Provider (SMTP + Attachment)"]
    end

    Dispatcher --> P_Slack
    Dispatcher --> P_Teams
    Dispatcher --> P_GChat
    Dispatcher --> P_Email

    P_Slack --> |POST Webhook| SlackAPI["Slack Workspace"]
    P_Teams --> |POST Webhook| TeamsAPI["Microsoft 365 Tenant"]
    P_GChat --> |POST Webhook| GChatAPI["Google Workspace Space"]
    P_Email --> |SMTP TLS| MailServer["Corporate Mail Server"]
```

---

## 5. Multi-Tenant Architecture & Data Isolation

```mermaid
flowchart TD
    subgraph AuthContext ["Authenticated Request Context"]
        User["User (JWT Authenticated)"]
        Header["X-Organization-ID Header"]
    end

    subgraph TenantGuard ["Tenant Context Dependency (get_tenant_context)"]
        Verify["Validate Organization Membership (DB Check)"]
        RoleCheck["Extract Tenant Role (OWNER / ADMIN / FINOPS_MANAGER / ANALYST / VIEWER)"]
    end

    subgraph DataIsolation ["Tenant-Isolated Resources"]
        CostRecs["CostRecords (organization_id)"]
        Reports["Reports & Storage (reports/{organization_id}/...)"]
        Alerts["AlertRules & AnomalyEvents (organization_id)"]
        Recs["OptimizationRecommendations (organization_id)"]
        Integrations["NotificationIntegrations (organization_id)"]
    end

    User --> Header --> Verify --> RoleCheck
    RoleCheck --> CostRecs & Reports & Alerts & Recs & Integrations
```

---

## 6. Security & Isolation Principles

1. **Decoupled Provider Interface**: The core application logic does not contain `import boto3` directly. All AWS SDK interactions occur strictly inside `app/providers/aws/`.
2. **Server-Enforced Multi-Tenancy**: Every authenticated request passes through `get_tenant_context` which validates active membership in `organization_members`. Requests without authorized tenant membership return `403 Forbidden`. Frontend-supplied tenant IDs are never trusted without DB validation.
3. **Centralized RBAC & Permission Matrix**: Organization access is governed by 5 distinct roles (`OWNER`, `ADMIN`, `FINOPS_MANAGER`, `ANALYST`, `VIEWER`). Granular permissions are declared in `app/auth/permissions.py` and enforced via `RequirePermission(PERM_NAME)` dependency guards.
4. **Session Management & Token Revocation**: Active user sessions are tracked in `user_sessions` with device and IP metadata. Refresh tokens are hashed in DB (SHA-256) and support instantaneous single-session (`DELETE /auth/sessions/{id}`) or global session revocation (`POST /auth/logout-all`).
5. **Owner & Role Escalation Protection**: The system prevents demoting or removing the last organization `OWNER`. Users cannot escalate their own privileges or grant roles exceeding their own role level.
6. **Zero-Trust Report Downloads & Path Traversal Prevention**: Download endpoints validate tenant ownership (`organization_id`), verify file existence within sanitized `output_base` boundaries (`resolve_safe_file_path`), and stream files safely to prevent cross-tenant data leakage or directory traversal.
7. **Financial Precision**: No binary floating-point types (`float`) are permitted for currency values in database tables or financial operations. All calculations use Python `decimal.Decimal` and PostgreSQL `NUMERIC(18, 4)`.
8. **Defensive HTTP Security & Hardened CORS**: FastAPI middleware enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, and `Strict-Transport-Security (HSTS)`. CORS methods and headers are explicitly whitelisted.
9. **Password Complexity & Strength Enforcement**: Passwords must contain a minimum of 8 characters, with at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character.
10. **Guarded Route Navigation & Production Demo Control**: `PublicOnlyRoute` protects public authentication views from flickering for logged-in users. Quick Demo credentials are hidden in production unless `DEMO_MODE=true` or explicitly requested via `?demo=true`.

---

## 7. Security Permission Matrix

| Capability | OWNER | ADMIN | FINOPS_MANAGER | ANALYST | VIEWER |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **organization.read** | YES | YES | YES | YES | YES |
| **organization.update** | YES | YES | NO | NO | NO |
| **members.read** | YES | YES | YES | YES | YES |
| **members.invite** | YES | YES* | NO | NO | NO |
| **members.update** | YES | YES* | NO | NO | NO |
| **members.remove** | YES | YES* | NO | NO | NO |
| **aws_accounts.read** | YES | YES | YES | YES | YES |
| **aws_accounts.manage** | YES | YES | NO | NO | NO |
| **costs.read** | YES | YES | YES | YES | YES |
| **costs.export** | YES | YES | YES | YES | NO |
| **reports.read** | YES | YES | YES | YES | YES |
| **reports.create** | YES | YES | YES | YES | NO |
| **reports.download** | YES | YES | YES | YES | NO |
| **reports.delete** | YES | YES | NO | NO | NO |
| **optimization.read** | YES | YES | YES | YES | YES |
| **optimization.manage** | YES | YES | YES | NO | NO |
| **alerts.read / budgets.read** | YES | YES | YES | YES | YES |
| **alerts.manage / budgets.manage** | YES | YES | YES | NO | NO |
| **integrations.manage** | YES | YES | NO | NO | NO |
| **settings.update** | YES | YES | NO | NO | NO |

*\*Role escalation protection prevents ADMIN from inviting or promoting users to OWNER role. The last organization OWNER cannot be removed or demoted.*

---

## 8. Multi-Currency Telemetry & Real-Time Exchange Rates

The platform provides seamless multi-currency display capabilities for global FinOps teams:

```mermaid
flowchart LR
    subgraph RateSource ["External Exchange Rate API"]
        OpenER["https://open.er-api.com/v6/latest/USD"]
    end

    subgraph CurrencyContext ["Frontend CurrencyContext"]
        Store["localStorage ('preferred_currency', 'usd_inr_rate')"]
        State["State: USD ($) / INR (₹)"]
        Formatter["formatCurrency(amount, decimals)"]
    end

    subgraph UI ["Dashboard & Telemetry Components"]
        HeaderToggle["Header Currency Switcher [$ USD | ₹ INR]"]
        CostCards["KPI Scorecards & Summary Cards"]
        Tables["Services, Accounts, Regions & Costs Tables"]
    end

    OpenER -->|Live Fetch| CurrencyContext
    HeaderToggle -->|Set Currency| State
    State --> Formatter
    Formatter --> CostCards & Tables
```

1. **Live Exchange Rate Engine**: Fetches real-time USD/INR rates from Open Exchange Rates API (`open.er-api.com`) with caching in `localStorage` (`usd_inr_rate`) and fallback rate `83.5`.
2. **Global Telemetry Formatting**: `formatCurrency()` formats numbers according to `en-IN` (Indian Rupees `₹`) or `en-US` (US Dollars `$`) locale standards.
3. **One-Click Header Switcher**: Header component features an interactive `[$ USD | ₹ INR]` switcher with live rate tooltips.



