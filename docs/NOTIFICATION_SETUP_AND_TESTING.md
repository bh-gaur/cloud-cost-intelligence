# Notification Setup and Testing Guide

This guide provides step-by-step instructions for configuring, testing, and troubleshooting the two active notification channels in **AWS Cost Intelligence**:

1. **Email (SMTP + HTML Reports & Attachments)**
2. **Slack (Block Kit Webhooks)**

---

## 1. Architecture Overview

Notifications can be triggered through four primary workflows:

1. **CLI Script (`backend/scripts/send_report.py`)**: For automated cron jobs and manual CLI dispatches.
2. **Daily Anomaly Detector (`backend/app/alerts/detector.py`)**: Automatically fires when anomalous spend is detected.
3. **REST API (`POST /api/v1/notifications/test`)**: Health check and test dispatch endpoint.
4. **Web UI (`/integrations` and `/settings`)**: 1-click test buttons for administrators.

---

## 2. Setting Up Email (SMTP)

The platform supports any standard SMTP provider with TLS support (e.g., Gmail, Amazon SES, SendGrid, Mailtrap, or a local mock SMTP server).

### A. Environment Configuration

Add the following variables to your `.env` file (in the project root):

```ini
# SMTP Server Settings
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your-16-char-app-password"
SMTP_FROM="AWS Cost Intelligence <your-email@gmail.com>"

# Destination Email Addresses (comma-separated)
EMAIL_RECIPIENTS="your-email@gmail.com"
```

### B. Common Provider Configurations

#### Option 1: Gmail (Quick Personal Testing)

1. Ensure **2-Step Verification** is enabled on your Google Account.
2. Go to **Google Account Settings** -> **Security** -> **App Passwords**.
3. Generate a new App Password (name it `CloudCostIntelligence`).
4. Configure `.env`:
   ```ini
   SMTP_HOST="smtp.gmail.com"
   SMTP_PORT=587
   SMTP_USERNAME="yourname@gmail.com"
   SMTP_PASSWORD="your-16-char-app-password"
   SMTP_FROM="AWS Cost Intelligence <yourname@gmail.com>"
   EMAIL_RECIPIENTS="yourname@gmail.com"
   ```

#### Option 2: Amazon SES (Production AWS Environment)

1. In the AWS SES Console, create and verify your sender domain/email identity.
2. Go to **SMTP Settings** -> **Create SMTP Credentials**.
3. Copy the generated SMTP Username and Password.
4. Configure `.env`:
   ```ini
   SMTP_HOST="email-smtp.us-east-1.amazonaws.com"
   SMTP_PORT=587
   SMTP_USERNAME="AKIAEXAMPLEUSER"
   SMTP_PASSWORD="BJExamplePasswordSecretKey"
   SMTP_FROM="AWS Cost Intelligence <verified-sender@yourdomain.com>"
   EMAIL_RECIPIENTS="team@yourdomain.com"
   ```

#### Option 3: Mailtrap / Local SMTP (Zero-Risk Sandbox)

To test email sending locally without delivering to real inboxes, use Mailtrap:

```ini
SMTP_HOST="sandbox.smtp.mailtrap.io"
SMTP_PORT=2525
SMTP_USERNAME="your_mailtrap_username"
SMTP_PASSWORD="your_mailtrap_password"
SMTP_FROM="finops@example.com"
EMAIL_RECIPIENTS="dev-test@example.com"
```

---

## 3. Setting Up Slack Webhooks

Slack notifications use incoming webhooks formatted with rich **Block Kit** cards, colored variance badges, and KPI breakdowns.

### Steps to Create a Slack Webhook:

1. Navigate to **[Slack API Apps](https://api.slack.com/apps)** and click **Create New App** -> **From Scratch**.
2. Name your app `AWS Cost Intelligence` and pick your workspace.
3. Go to **Incoming Webhooks** in the sidebar and toggle **Activate Incoming Webhooks** to **On**.
4. Click **Add New Webhook to Workspace** at the bottom.
5. Select the target channel (e.g. `#finops-alerts` or a private test channel) and click **Allow**.
6. Copy the generated **Webhook URL**.
7. Add to your `.env`:
   ```ini
   SLACK_WEBHOOK_URL="https://hooks.slack.com/services/your/webhook/url"
   ```

---

## 4. How to Test Notifications

### Method 1: Testing via CLI (Recommended)

The project includes `backend/scripts/send_report.py` to test and dispatch notifications directly from your terminal.

#### 1. Dry-Run Validation (Checks readiness without sending network calls):

```bash
# Validate Email
python backend/scripts/send_report.py --channel email --dry-run

# Validate Slack
python backend/scripts/send_report.py --channel slack --dry-run

# Validate All Active Channels
python backend/scripts/send_report.py --channel all --dry-run
```

#### 2. Live Dispatch:

```bash
# Send test summary to Slack
python backend/scripts/send_report.py --channel slack

# Send test summary to Email
python backend/scripts/send_report.py --channel email

# Send email WITH generated HTML report attached
python backend/scripts/send_report.py --channel email --report-file backend/reports/html/aws-cost-report.html

# Dispatch across both Email and Slack simultaneously
python backend/scripts/send_report.py --channel all
```

---

### Method 2: Testing via REST API (`curl`)

When the backend API server is running (`uvicorn app.main:app` or `docker compose up backend`):

#### 1. Check Channel Health Status

```bash
curl -X GET "http://localhost:8000/api/v1/notifications/status" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "X-Organization-ID: <ORG_ID>"
```

**Expected Response:**

```json
{
  "success": true,
  "data": {
    "email": {
      "healthy": true,
      "message": "Connected to SMTP server smtp.gmail.com:587"
    },
    "slack": {
      "healthy": true,
      "message": "Slack webhook configured and ready."
    }
  }
}
```

#### 2. Trigger a Test Dispatch

```bash
# Test Email
curl -X POST "http://localhost:8000/api/v1/notifications/test" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  -H "X-Organization-ID: <ORG_ID>" \
  -d '{"channel_type": "email"}'

# Test Slack
curl -X POST "http://localhost:8000/api/v1/notifications/test" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  -H "X-Organization-ID: <ORG_ID>" \
  -d '{"channel_type": "slack"}'
```

---

### Method 3: Testing from the Web UI

1. Start both backend and frontend servers:

   ```bash
   # Terminal 1 - Backend
   cd backend && python -m uvicorn app.main:app --reload --port 8000

   # Terminal 2 - Frontend
   cd frontend && npm run dev
   ```

2. Log in to the dashboard at `http://localhost:5173`.
3. In the sidebar, navigate to **Integrations**.
4. Scroll down to **Alert Dispatch Channels**:
   - On the **Email / SMTP** card, click **Test Connection** (sends a verification email to `EMAIL_RECIPIENTS`).
   - On the **Slack Webhook** card, click **Test Connection** (sends a verification alert to your Slack channel).
5. A green toast banner will appear confirming successful delivery.

---

### Method 4: Automated Unit Tests (Pytest)

Run the backend test suite to verify notification validation, health checking, and channel restrictions:

```bash
cd backend
pytest tests/test_notifications.py -v
```

**Verified Test Scenarios:**

- Validates Slack webhook URL formatting (rejects non-HTTPS / malformed endpoints).
- Performs live health check inspection without leaking credentials.
- Confirms rejection of unsupported notification channels.

---

## 5. Troubleshooting & FAQs

| Symptom                                     | Cause                        | Solution                                                                                                            |
| :------------------------------------------ | :--------------------------- | :------------------------------------------------------------------------------------------------------------------ |
| `SMTPAuthenticationError (535)`             | Invalid username or password | If using Gmail, you must use a 16-character **App Password**, not your primary login password.                      |
| `SMTPConnectError / Timeout`                | Firewall or wrong port       | Verify `SMTP_PORT=587` with STARTTLS. Avoid port `25` on cloud hosts as many ISPs/cloud providers block it.         |
| `Slack Webhook 404 / 403`                   | Revoked or disabled webhook  | Regenerate the webhook URL in the Slack App management console and update `.env`.                                   |
| `Email provider invoked but not configured` | Missing `.env` entries       | Ensure both `SMTP_HOST` and `EMAIL_RECIPIENTS` are populated in `.env`.                                             |
| `Recipients not receiving email`            | Spam folder or SES sandbox   | Check the spam/junk folder. In Amazon SES sandbox mode, recipient email addresses must also be verified identities. |
