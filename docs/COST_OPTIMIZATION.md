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

## The 6 Core Optimization Rules

| Rule ID | Rule Name | Target Service | Evaluation Logic | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| **OPT-001** | EC2 Idle Instances | Amazon EC2 | Average CPU utilization < 5% over 7 days, negligible network I/O. | Observed |
| **OPT-002** | Unattached EBS Volumes | Amazon EBS | Volumes in `available` state (not attached to any running or stopped EC2 instance). | Observed |
| **OPT-003** | Unassociated Elastic IPs | Amazon EC2 | Elastic IP addresses allocated but not attached to any running resource. | Observed |
| **OPT-004** | S3 Buckets Without Lifecycle Policies | Amazon S3 | S3 buckets lacking lifecycle policies to transition objects to Intelligent-Tiering / Glacier. | Potential |
| **OPT-005** | Untagged Resource Compliance | Multi-Service | Resources lacking mandatory FinOps cost-allocation tags (`Environment`, `Team`, `Application`). | Potential |
| **OPT-006** | Orphaned Snapshots | Amazon EBS / RDS | Automated or manual snapshots older than 90 days. | Observed |

