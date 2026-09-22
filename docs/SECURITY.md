# Security Policy & Architecture

## Security Objectives
The **AWS Cost Intelligence** platform processes financial spend metrics, cloud resource metadata, and organizational hierarchy information. Our security architecture strictly implements:
1. **Least Privilege Read-Only Access**: Zero write permissions to client AWS infrastructure.
2. **Strict Cryptographic Credential Isolation**: No storage or exposure of plaintext secrets or AWS long-lived access keys.
3. **Monetary Data Integrity**: All financial calculations use arbitrary-precision decimals (`Decimal`/`NUMERIC(18, 4)`) to eliminate floating-point inaccuracies.
4. **Auditability**: Complete structured logging of authentication events, report exports, configuration alterations, and connection diagnostics.

---

## AWS IAM Security & Cross-Account Role Architecture

The preferred and recommended production configuration is **Cross-Account IAM Role Assumption with External ID**.

### 1. Minimal IAM Policy (Read-Only)
The platform requires only read-only access to Cost Explorer, AWS Budgets, Cost Anomaly Detection, and specific resource metadata needed for cost optimization:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CostExplorerReadOnly",
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostAndUsageWithResources",
        "ce:GetDimensionValues",
        "ce:GetCostForecast",
        "ce:GetAnomalies",
        "ce:GetAnomalySubscriptions",
        "ce:GetAnomalyMonitors",
        "ce:GetSavingsPlansUtilization",
        "ce:GetSavingsPlansCoverage",
        "ce:GetReservationUtilization",
        "ce:GetReservationCoverage"
      ],
      "Resource": "*"
    },
    {
      "Sid": "BudgetsReadOnly",
      "Effect": "Allow",
      "Action": [
        "budgets:ViewBudget",
        "budgets:DescribeBudgets",
        "budgets:DescribeBudgetPerformanceHistory"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ResourceOptimizationMetadataReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots",
        "ec2:DescribeAddresses",
        "ec2:DescribeNatGateways",
        "rds:DescribeDBInstances",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketLifecycleConfiguration",
        "logs:DescribeLogGroups",
        "cloudwatch:GetMetricData",
        "tag:GetResources",
        "tag:GetTagKeys"
      ],
      "Resource": "*"
    },
    {
      "Sid": "OrganizationsReadOnly",
      "Effect": "Allow",
      "Action": [
        "organizations:DescribeOrganization",
        "organizations:ListAccounts"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. IAM Role Trust Policy (With External ID)
To protect against the Confused Deputy problem in multi-tenant environments:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::PLATFORM_ACCOUNT_ID:role/FinOpsWorkerExecutionRole"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "UNIQUE_TENANT_EXTERNAL_ID_2026"
        }
      }
    }
  ]
}
```

---

## Authentication & Session Security

- **Password Storage**: Passwords are cryptographically salted and hashed using `bcrypt` (work factor 12). Plaintext passwords are never logged or stored.
- **JWT Lifecycles**:
  - Access Token: short-lived (60 minutes).
  - Refresh Token: rotation with 7-day expiration.
- **Role-Based Access Control (RBAC)**:
  - `OWNER`: Complete control over organization, members, AWS account connection/deletion, notification channels, and tenant settings.
  - `ADMIN`: Full management access to members, invitations, AWS accounts, alert channels, cost exports, and audit logs.
  - `FINOPS_MANAGER`: Management access to cost optimization scans, alert rules creation, report creation/downloads, cost exports, and member role management (up to manager level), with role escalation protections preventing assignment of `ADMIN` or `OWNER` roles.
  - `ANALYST`: Access to dashboards, cost tables, report generation & downloads, and cost exports. Restricted from deletion and account connection.
  - `VIEWER`: Strict read-only access across dashboards, cost exploration, and recommendations. Restricted from creating/deleting AWS accounts, alert rules, notification channels, reports, or members.

---

## Safe Data Handling & Injection Protections

1. **SQL Injection Defense**: All database queries utilize SQLAlchemy ORM parameterized queries. Raw string concatenation in SQL is prohibited.
2. **Directory Traversal Protection**: Report download and local file storage endpoints strictly sanitize file identifiers using UUID validation and resolve canonical paths to ensure they stay confined to the designated `reports/` folder.
3. **HTML Sanitization**: HTML reports generated with Jinja2 use strict auto-escaping to eliminate XSS vectors when rendering user-defined tags or names.
4. **Secret Masking**: Webhook URLs, SMTP passwords, and AWS credentials are masked (`****1234`) in all API responses and audit logs.

---

## Vulnerability Reporting

If you discover a security vulnerability, please submit an advisory directly to `security@cloudcostintelligence.internal` rather than filing a public issue.

