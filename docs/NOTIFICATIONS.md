# Notification Integrations Specification

## Overview

The notification subsystem dispatches daily/weekly cost summaries, anomaly alerts, budget threshold breaches, and scheduled reports across 2 distinct channels:
1. **Email (SMTP)**
2. **Slack**

---

## Channel Configurations

### 1. Slack (Block Kit)
Configured with an incoming webhook URL. Sends formatted Block Kit payloads with colored status indicators:
- Environment variable: `SLACK_WEBHOOK_URL`
- Supported features: Today's Spend vs Yesterday, Top Cost Driving Services, Anomaly Warnings, and Savings Summary.

### 2. Email (SMTP + Attachments)
Direct SMTP connection with TLS support. Supports embedding summaries in HTML body and attaching CSV/HTML report files:
- Environment variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `EMAIL_RECIPIENTS`.

---

## Security & Sanitization Rules

- **Zero Credential Leaks**: Webhook URLs and SMTP passwords are obfuscated in UI forms (e.g. `https://hooks.slack.com/services/****/****`).
- **No Fake Success**: A notification is only marked as "SENT" if the remote server returns a `2xx` HTTP status or the SMTP server accepts the message delivery.

---

## Detailed Setup & Testing Guide

For complete step-by-step setup instructions, Gmail/SES/Mailtrap configurations, CLI test commands, and curl examples, see:
- [Notification Setup and Testing Guide](file:///Users/vishnu/learning/b_github/cloud-cost-intelligence/docs/NOTIFICATION_SETUP_AND_TESTING.md)

