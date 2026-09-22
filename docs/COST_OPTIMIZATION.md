# Cost Optimization Engine & Rules Specification

## Overview

The Cost Optimization Engine continuously evaluates AWS resource states, pricing dimensions, and utilization metrics to generate actionable FinOps recommendations.

---

## FinOps Recommendation Principles

1. **No Guaranteed Savings Claim**: Savings are classified under clear confidence levels:
   - **Observed**: Confirmed directly from resource state (e.g. unattached EBS volume, idle unassociated EIP).
   - **Estimated**: Modeled against sizing benchmarks (e.g. right-sizing compute instances based on peak CPU/memory).
   - **Potential**: Subject to architectural changes (e.g. converting S3 Standard to Intelligent-Tiering).
2. **Validation Status**:
   - `Requires validation`: Action needed by DevOps/SRE before terminating or modifying.
   - `Insufficient data`: Usage metrics have fewer than 14 days of history.

---

## The 11 Core Optimization Rules

| Rule ID | Rule Name | Target Service | Evaluation Logic | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| **OPT-001** | EC2 Idle Instances | Amazon EC2 | Average CPU utilization < 5% over 7 days, negligible network I/O. | Observed |
| **OPT-002** | EC2 Rightsizing | Amazon EC2 | Peak CPU < 30% and Memory < 40%; recommend downgrading 1 family tier. | Estimated |
| **OPT-003** | Unattached EBS Volumes | Amazon EBS | Volumes in `available` state (not attached to any running or stopped EC2 instance). | Observed |
| **OPT-004** | RDS Rightsizing | Amazon RDS | Database CPU < 15% and connection count < 5 over sustained 14-day window. | Estimated |
| **OPT-005** | S3 Intelligent-Tiering | Amazon S3 | S3 buckets with >1TB standard storage and infrequent access patterns. | Potential |
| **OPT-006** | NAT Gateway Optimization | Amazon VPC | NAT Gateways processing <1GB per day or cross-AZ redundant gateways with minimal traffic. | Observed |
| **OPT-007** | CloudWatch Log Retention | Amazon CloudWatch | Log groups configured with `Never Expire` retention accumulating GBs of legacy logs. | Estimated |
| **OPT-008** | Orphaned Snapshots | Amazon EC2 / RDS | Automated or manual snapshots older than 90 days whose source volumes no longer exist. | Observed |
| **OPT-009** | Untagged Resource Compliance | Multi-Service | Resources lacking mandatory FinOps tags (`Environment`, `Team`, `Owner`, `Project`). | Potential |
| **OPT-010** | Compute Savings Plans | AWS Savings Plans | Steady on-demand baseline spend evaluated for 1-year or 3-year commitments. | Estimated |
| **OPT-011** | Reserved Instance Coverage | Amazon RDS / OpenSearch | 24/7 steady database instances without active RI reservations. | Estimated |

