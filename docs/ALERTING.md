# Alerting & Anomaly Detection Specification

## Overview

The alerting subsystem identifies unexpected cost surges, monitors threshold limits, and checks budget forecasts before month-end invoices arrive.

---

## 1. Anomaly Detection Engine

The anomaly detection engine runs periodically or on-demand:
1. **Statistical Rolling Baseline**:
   - Calculates the 14-day rolling mean ($\mu$) and standard deviation ($\sigma$) of daily spend per AWS service and account.
   - Triggers an anomaly event when today's spend exceeds:
     $$\text{Threshold} = \mu + 2.5 \cdot \sigma$$
2. **Absolute Spike Threshold**:
   - Flags any single service that increases by more than \$250 or 30% day-over-day.
3. **New Service Discovery**:
   - Detects when an AWS service that had zero spend over the preceding 30 days suddenly incurs billable charges.

---

## 2. AWS Budgets Integration

For organizations utilizing native AWS Budgets:
- Synchronizes defined budget limits (e.g. Monthly Total, Production Account, RDS Spend).
- Calculates consumption percentage:
  $$\text{Utilization} = \left( \frac{\text{Current Spend}}{\text{Budget Limit}} \right) \times 100\%$$
- Health status thresholds:
  - **Healthy**: $<80\%$ utilized.
  - **Warning**: $80\% - 95\%$ utilized.
  - **Critical**: $95\% - 100\%$ utilized.
  - **Exceeded**: $>100\%$ utilized.

