# AWS Cost Intelligence Platform (`cloud-cost-intelligence`)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](backend/)
[![React](https://img.shields.io/badge/React-18%2B-cyan)](frontend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production%20Ready-green)](backend/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](docker-compose.yml)

**AWS Cost Intelligence** is an enterprise-grade, full-stack FinOps cloud cost management and optimization platform. Engineered with a clean **Cloud Provider Abstraction**, it monitors daily AWS cloud spend, computes day-over-day cost variances, drills down across multi-account AWS Organizations and regions, runs 11+ automated optimization rules, detects anomalous spend spikes, tracks AWS Budgets, and generates multi-format executive reports (CSV, JSON, print-friendly HTML) dispatched via Slack, Teams, Google Chat, and Email.

---

## Key Features

- **Executive FinOps Dashboard**:
  - Immediate visibility into **Today's Cost**, **Yesterday's Cost**, and **Day Before Yesterday's Cost**.
  - Absolute currency differentials and percentage variance badges with up/down indicators.
  - Interactive multi-period trend visualizations (Daily Line Chart, Weekly/Monthly Bar Chart, Service Donut Chart, and Spend Scatter Plot).
  - Centralized, deterministic color registry ensuring consistent AWS service hues across all renders.
  - Multi-account AWS Organizations and regional concentration heatmaps.
  - Tagging coverage metrics and untagged infrastructure cost breakdown.
- **Deep Cost Exploration & Streaming Export**:
  - Filterable, searchable, sortable, and paginated Cost Records table.
  - Live filter-aware streaming CSV downloads for multi-gigabyte datasets.
- **Automated Cost Optimization Engine**:
  - 11 modular, rule-based analyzers identifying idle, over-provisioned, or misconfigured cloud resources:
    1. EC2 Idle Instances (CPU < 5%)
    2. EC2 Rightsizing
    3. Unattached EBS Volumes (`available` status)
    4. Over-provisioned RDS Instances
    5. S3 Lifecycle & Intelligent-Tiering Opportunities
    6. NAT Gateway Data Processing & Redundancy Optimization
    7. CloudWatch Log Group Retention Limits (flagging unbounded retention)
    8. Orphaned Snapshots (>90 days old)
    9. Untagged Infrastructure Compliance Detection
    10. Compute & EC2 Savings Plans Opportunities
    11. Reserved Instance (RI) Commitment Coverage
  - Standardized FinOps recommendation model with Confidence (`Observed`, `Estimated`, `Potential`) and Status (`Requires validation`, `Insufficient data`).
- **Anomaly Detection & AWS Budgets**:
  - Statistical deviation alerts (historical rolling baseline and configurable percentage spikes).
  - AWS Budgets integration displaying consumed percentage, forecasted end-of-month spend, and health statuses (`Healthy`, `Warning`, `Critical`, `Exceeded`).
- **Multi-Format Reporting & Local Archival**:
  - Automated generation of CSV, JSON, and styled print-ready HTML reports.
  - Local disk storage with 90-day retention policies (`REPORT_RETENTION_DAYS=90`).
- **Multi-Channel Notification Dispatcher**:
  - Slack Block Kit webhooks with formatted KPI metrics and anomaly warnings.
  - Microsoft Teams Adaptive Card webhooks.
  - Google Chat Card v2 webhooks.
  - SMTP Email notifications with attached reports.
- **Authentication, Authorization & Multi-Tenant Access Control**:
  - **Multi-Tenancy & Tenant Isolation**: Strict server-side organization boundaries (`X-Organization-ID` header validation against database `organization_members`). Never trusts frontend-supplied tenant IDs.
  - **Centralized Role-Based Access Control (RBAC)**: 5 organization roles (`OWNER`, `ADMIN`, `FINOPS_MANAGER`, `ANALYST`, `VIEWER`) mapped centrally to granular permissions (`costs.read`, `costs.export`, `reports.download`, `members.invite`, `aws_accounts.manage`, etc.).
  - **Session Management & Token Revocation**: Active `user_sessions` tracking with device/IP metadata. Supports `/auth/logout`, `/auth/logout-all` (all devices signout), and `/auth/sessions` management.
  - **IDOR & Resource Ownership Protection**: Server-side verification of resource ownership (`report.organization_id == active_org_id`, `account.organization_id == active_org_id`). Safe file streaming preventing path traversal.
  - **Owner & Role Escalation Protection**: Prevents removing or demoting the last organization `OWNER`. Prevents users from escalating their own privileges or assigning roles higher than their own level.
  - **Secure Password & Token Security**: Password strength validation, bcrypt hashing (rounds=12), generic login failure messages, single-use cryptographically secure reset/verification tokens. Account enumeration protection on reset flows.

---

## Security Permission Matrix

| Capability | OWNER | ADMIN | FINOPS_MANAGER | ANALYST | VIEWER |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **View Dashboard / Costs** | YES | YES | YES | YES | YES |
| **Export Costs (CSV)** | YES | YES | YES | YES | NO |
| **View AWS Accounts** | YES | YES | YES | YES | YES |
| **Manage AWS Accounts** | YES | YES | NO | NO | NO |
| **Generate Reports** | YES | YES | YES | YES | NO |
| **Download Reports** | YES | YES | YES | YES | NO |
| **Delete Reports** | YES | YES | NO | NO | NO |
| **Manage Optimization** | YES | YES | YES | NO | NO |
| **Manage Alerts & Budgets** | YES | YES | YES | NO | NO |
| **Manage Integrations** | YES | YES | NO | NO | NO |
| **View Members** | YES | YES | YES | YES | YES |
| **Invite & Manage Members** | YES | YES* | NO | NO | NO |
| **Organization Settings** | YES | YES | NO | NO | NO |

*\*Role escalation protection prevents ADMIN from promoting members to OWNER. Last OWNER cannot be removed or demoted.*
- **Demo Mode**:
  - Out-of-the-box exploration without live AWS credentials (`DEMO_MODE=true`), clearly displaying `DEMO DATA` indicators.

---

## Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18+, TypeScript, Vite, Tailwind CSS, TanStack Query, Recharts, Lucide Icons |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, Boto3 |
| **Database** | PostgreSQL 16 (production), SQLite (local zero-setup mode) |
| **Container** | Docker, Docker Compose |
| **Testing** | Pytest, Vitest / React Testing Library |
| **Code Quality** | Ruff, Black, ESLint, Prettier |

---

## Quick Start (Local Setup)

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (optional, for containerized run)

### 1. Clone & Configure Environment
```bash
cp .env.example .env
```
*(By default, `DEMO_MODE=true` is enabled, allowing immediate testing with realistic mock data!)*

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r pyproject.toml # or make install
python scripts/seed_demo_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI backend will start at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

### 3. Frontend Setup
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
The React frontend will start at `http://localhost:5173`.

---

## Docker Compose Quick Start

To launch the complete platform (PostgreSQL 16, Backend API, and Frontend) in Docker:
```bash
docker compose up --build -d
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## Default Demo Credentials

When initialized in Demo Mode or after running `seed_demo_data.py`, you can log in with:

| Role | Email | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin@cloudcost.local` | `Admin123!@#` |
| **FinOps User** | `user@cloudcost.local` | `User123!@#` |

---

## Standalone CLI Scripts

The platform includes standalone CLI utilities under `backend/scripts/`:

```bash
# Fetch and synchronize AWS costs (or mock costs)
python backend/scripts/fetch_costs.py --provider mock --start-date 2026-09-01 --end-date 2026-09-12

# Generate reports in CSV, JSON, or print-ready HTML
python backend/scripts/generate_report.py --format html --output-dir backend/reports/html/

# Dispatch reports to alert channels
python backend/scripts/send_report.py --channel slack --dry-run

# Run anomaly detection algorithms
python backend/scripts/detect_anomalies.py

# Run all 11+ optimization rules and refresh recommendations
python backend/scripts/generate_optimizations.py
```

---

## Documentation Directory

For in-depth architectural and operational guides, refer to:
- [API Reference](docs/API.md)
- [AWS IAM & Configuration](docs/AWS.md)
- [Database Schema & Data Models](docs/DATABASE.md)
- [Deployment Guide (ECS / EKS / Docker)](docs/DEPLOYMENT.md)
- [Reporting Engine & Templates](docs/REPORTING.md)
- [Notification Integrations](docs/NOTIFICATIONS.md)
- [Cost Optimization Rule Engine](docs/COST_OPTIMIZATION.md)
- [Alerting & Anomaly Detection](docs/ALERTING.md)
- [Troubleshooting & Diagnostics](docs/TROUBLESHOOTING.md)
- [Security Architecture](SECURITY.md)
- [System Architecture](ARCHITECTURE.md)
- [Agent & Developer Guidelines](AGENTS.md)

