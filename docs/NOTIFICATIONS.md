# Notification Integrations Specification

## Overview

The notification subsystem dispatches daily/weekly cost summaries, anomaly alerts, budget threshold breaches, and scheduled reports across 4 distinct channels:
1. **Email (SMTP)**
2. **Slack**
3. **Google Chat**
4. **Microsoft Teams**

---

## Channel Configurations

### 1. Slack (Block Kit)
Configured with an incoming webhook URL. Sends formatted Block Kit payloads with colored status indicators:
- Environment variable: `SLACK_WEBHOOK_URL`
- Supported features: Today's Spend vs Yesterday, Top Cost Driving Services, Anomaly Warnings, and Savings Summary.

### 2. Microsoft Teams (Adaptive Cards)
Sends JSON Adaptive Cards v1.4 via Office 365 / Power Automate webhook:
- Environment variable: `TEAMS_WEBHOOK_URL`
- Features: Key-value FactSets, clickable deep links to the FinOps dashboard, and warning callouts for budget breaches.

### 3. Google Chat (Cards v2)
Dispatches formatted Cards v2 with header, section widgets, and key-value metrics:
- Environment variable: `GCHAT_WEBHOOK_URL`

### 4. Email (SMTP + Attachments)
Direct SMTP connection with TLS support. Supports embedding summaries in HTML body and attaching CSV/HTML report files:
- Environment variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `EMAIL_RECIPIENTS`.

---

## Security & Sanitization Rules

- **Zero Credential Leaks**: Webhook URLs and SMTP passwords are obfuscated in UI forms (e.g. `https://hooks.slack.com/services/****/****`).
- **No Fake Success**: A notification is only marked as "SENT" if the remote server returns a `2xx` HTTP status or the SMTP server accepts the message delivery.

