# System Setup & Configuration Guide

This guide details the steps required to configure and run the AWS Cost Intelligence & Multi-Tenant FinOps Platform.

---

## 🤖 AUTOMATED STEPS (Quickstart Local Setup)

To spin up the entire application locally using standard Python and Node.js toolchains:

```bash
# 1. Clone repository & navigate to workspace
git clone https://github.com/org/cloud-cost-intelligence.git
cd cloud-cost-intelligence

# 2. Setup Python virtual environment & install backend dependencies
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Setup Frontend dependencies
cd frontend
npm install
cd ..

# 4. Initialize Database Schema & Seed Baseline Roles/Users
./backend/venv/bin/python3 backend/scripts/seed_demo_data.py

# 5. Start Backend API Server (Port 8000)
./backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend

# 6. Start Frontend Dev Server (Port 5173) in a separate terminal
cd frontend && npm run dev
```

---

## 🛠 MANUAL STEPS (Production Configuration)

The following steps **cannot be automated** and must be performed manually in your cloud provider and infrastructure accounts.

### 1. AWS IAM Role Creation (Cross-Account Access)
To allow the FinOps platform to ingest Cost Explorer data from your AWS Organization:

1. Log into your **AWS Management Console** (Payer/Management Account).
2. Navigate to **IAM -> Roles -> Create Role**.
3. Select **Another AWS Account** as the trusted entity:
   - Account ID: `<FINOPS_PLATFORM_AWS_ACCOUNT_ID>`
   - Select **Require external ID**: Enter your organization's external ID (e.g., `finops-tenant-prod-2026`).
4. Attach the following AWS Managed Policies:
   - `AWSCostExplorerReadOnlyAccess`
   - `AWSBudgetsReadOnlyAccess`
5. Name the role `FinOpsCostExplorerReadOnlyRole` and create it.
6. Note down the **Role ARN** (e.g. `arn:aws:iam::123456789012:role/FinOpsCostExplorerReadOnlyRole`).

---

### 2. Environment Variables (`.env`)
Create a `.env` file in the project root:

```env
# Server Core Settings
SECRET_KEY=change_this_to_a_secure_64_character_random_hex_string
ENVIRONMENT=production
ALLOWED_ORIGINS=https://app.finops.yourdomain.com

# Database Connection
DATABASE_URL=sqlite:///./cloud_cost.db
# For PostgreSQL: postgresql://user:password@localhost:5432/cloud_cost_db

# Security & Session Settings
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS Integration Settings
AWS_REGION=us-east-1
DEMO_MODE=false

# SMTP Email Notification Settings (Manual Setup)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM="AWS Cost Intelligence <your_email@gmail.com>"
EMAIL_RECIPIENTS="finops-alerts@yourdomain.com"

# Outbound Slack Webhook Integration (Manual Setup)
SLACK_WEBHOOK_URL=""
```

---

### 3. Outbound Notification Channels Setup

#### A. Slack Incoming Webhook
1. Go to `https://api.slack.com/apps` -> **Create New App**.
2. Enable **Incoming Webhooks**.
3. Click **Add New Webhook to Workspace**, select your alerts channel (e.g. `#finops-alerts`), and copy the Webhook URL.
4. Add to `.env` as `SLACK_WEBHOOK_URL` or configure under **Integrations** in the app UI.

#### B. SMTP Email Configuration
1. Obtain SMTP credentials from your email provider (e.g. Gmail App Password, AWS SES SMTP credentials, SendGrid, or Mailtrap).
2. Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `EMAIL_RECIPIENTS` in `.env`.

> For complete step-by-step instructions, Gmail/SES/Mailtrap configurations, CLI test scripts, and curl examples, see:
> [Notification Setup and Testing Guide](file:///Users/vishnu/learning/b_github/cloud-cost-intelligence/docs/NOTIFICATION_SETUP_AND_TESTING.md)
