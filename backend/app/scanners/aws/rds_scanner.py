"""
RDS Database Optimization & Waste Scanner
Detects idle RDS instances, Multi-AZ in non-production environments, gp2 to gp3 storage upgrades, and stale manual snapshots.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from app.scanners.base import BaseScanner, ScanFinding, ScanContext
from app.scanners.session import AWSSessionManager

logger = logging.getLogger(__name__)


class RDSScanner(BaseScanner):
    def __init__(self, context: ScanContext):
        super().__init__(context)
        self.session = AWSSessionManager.get_session(context.role_arn, context.external_id)

    def scan(self) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        for region in self.context.regions:
            try:
                rds = AWSSessionManager.get_client(self.session, "rds", region)
                cw = AWSSessionManager.get_client(self.session, "cloudwatch", region)

                findings.extend(self._scan_db_instances(rds, cw, region))
                findings.extend(self._scan_db_snapshots(rds, region))
            except Exception as e:
                logger.warning("RDS scanner encountered an issue in region %s: %s", region, e)
        return findings

    def _scan_db_instances(self, rds, cw, region: str) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        now = datetime.now(timezone.utc)
        lookback = now - timedelta(days=7)

        try:
            paginator = rds.get_paginator("describe_db_instances")
            for page in paginator.paginate():
                for db in page.get("DBInstances", []):
                    db_id = db["DBInstanceIdentifier"]
                    db_class = db["DBInstanceClass"]
                    engine = db["Engine"]
                    multi_az = db.get("MultiAZ", False)
                    status = db.get("DBInstanceStatus", "")
                    storage_type = db.get("StorageType", "gp2")
                    allocated_storage = db.get("AllocatedStorage", 20)
                    tags = {t.get("Key", ""): t.get("Value", "") for t in db.get("TagList", [])}
                    env = tags.get("Environment", tags.get("env", "")).lower()

                    monthly_cost = self._estimate_rds_cost(db_class, multi_az)

                    # 1. Idle database check (0 connections or <5% CPU)
                    if status == "available":
                        avg_conn = self._get_avg_metric(cw, "AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", db_id, lookback, now)
                        if avg_conn is not None and avg_conn < 1.0:
                            findings.append(ScanFinding(
                                rule_id="RDS-IDLE",
                                title=f"Idle RDS Database Instance: {db_id}",
                                description=f"Database {db_id} ({db_class}, {engine}) had an average of {avg_conn:.1f} connections over the past 7 days. Consider stopping or snapshotting and deleting.",
                                severity="HIGH" if monthly_cost > 150 else "MEDIUM",
                                category="IDLE_RESOURCE",
                                resource_type="RDS",
                                resource_id=db_id,
                                resource_name=db_id,
                                resource_arn=db.get("DBInstanceArn"),
                                region=region,
                                estimated_monthly_savings=monthly_cost,
                                current_monthly_cost=monthly_cost,
                                implementation_effort="medium",
                                operational_risk="high",
                                production_safety_score=60,
                                confidence="Observed",
                                remediation_steps=f"1. Verify database is no longer in use with application team\n2. Create final manual snapshot: aws rds create-db-snapshot --db-instance-identifier {db_id} --db-snapshot-identifier {db_id}-final-snapshot --region {region}\n3. Delete instance: aws rds delete-db-instance --db-instance-identifier {db_id} --skip-final-snapshot --region {region}",
                                remediation_code=f"aws rds stop-db-instance --db-instance-identifier {db_id} --region {region}",
                                resource_tags=tags,
                                raw_data={"db_class": db_class, "avg_connections_7d": avg_conn},
                            ))

                    # 2. Multi-AZ in Non-Production Environment
                    if multi_az and any(non_prod in env for non_prod in ["dev", "test", "stage", "staging", "sandbox"]):
                        single_az_cost = monthly_cost / 2.0
                        savings = monthly_cost - single_az_cost
                        findings.append(ScanFinding(
                            rule_id="RDS-MULTIAZ-NONPROD",
                            title=f"Multi-AZ Enabled in Non-Production RDS: {db_id}",
                            description=f"Database {db_id} is tagged '{env}' but has Multi-AZ enabled, doubling infrastructure cost. Converting to Single-AZ saves ~50% (${savings:.2f}/mo).",
                            severity="MEDIUM",
                            category="RIGHTSIZING",
                            resource_type="RDS",
                            resource_id=db_id,
                            resource_name=db_id,
                            resource_arn=db.get("DBInstanceArn"),
                            region=region,
                            estimated_monthly_savings=savings,
                            current_monthly_cost=monthly_cost,
                            implementation_effort="low",
                            operational_risk="low",
                            production_safety_score=90,
                            confidence="Estimated",
                            remediation_steps=f"Modify instance to Single-AZ: aws rds modify-db-instance --db-instance-identifier {db_id} --no-multi-az --apply-immediately --region {region}",
                            remediation_code=f"aws rds modify-db-instance --db-instance-identifier {db_id} --no-multi-az --apply-immediately --region {region}",
                            resource_tags=tags,
                            raw_data={"environment": env, "multi_az": True},
                        ))

                    # 3. Storage upgrade gp2 -> gp3
                    if storage_type == "gp2" and allocated_storage >= 100:
                        curr_storage_cost = allocated_storage * 0.115
                        gp3_storage_cost = allocated_storage * 0.092
                        savings = curr_storage_cost - gp3_storage_cost
                        findings.append(ScanFinding(
                            rule_id="RDS-STORAGE-GP3",
                            title=f"Upgrade RDS Storage to gp3: {db_id}",
                            description=f"Database {db_id} ({allocated_storage}GB) uses gp2 storage. Upgrading to gp3 reduces storage cost by 20% with higher baseline IOPS.",
                            severity="LOW",
                            category="MODERNIZATION",
                            resource_type="RDS",
                            resource_id=db_id,
                            resource_name=db_id,
                            resource_arn=db.get("DBInstanceArn"),
                            region=region,
                            estimated_monthly_savings=savings,
                            current_monthly_cost=curr_storage_cost,
                            implementation_effort="low",
                            operational_risk="low",
                            production_safety_score=95,
                            confidence="Estimated",
                            remediation_steps=f"Modify storage type: aws rds modify-db-instance --db-instance-identifier {db_id} --storage-type gp3 --apply-immediately --region {region}",
                            remediation_code=f"aws rds modify-db-instance --db-instance-identifier {db_id} --storage-type gp3 --apply-immediately --region {region}",
                            resource_tags=tags,
                            raw_data={"allocated_storage_gb": allocated_storage, "current_storage": "gp2"},
                        ))
        except Exception as e:
            logger.debug("Failed scanning RDS DB instances in %s: %s", region, e)
        return findings

    def _scan_db_snapshots(self, rds, region: str) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        now = datetime.now(timezone.utc)
        threshold_days = 90
        cutoff = now - timedelta(days=threshold_days)

        try:
            paginator = rds.get_paginator("describe_db_snapshots")
            for page in paginator.paginate(SnapshotType="manual"):
                for snap in page.get("DBSnapshots", []):
                    snap_id = snap["DBSnapshotIdentifier"]
                    create_time = snap.get("SnapshotCreateTime")
                    if create_time and create_time < cutoff:
                        size_gb = snap.get("AllocatedStorage", 20)
                        monthly_cost = size_gb * 0.095  # RDS snapshot storage ~$0.095/GB-mo

                        findings.append(ScanFinding(
                            rule_id="RDS-OLD-SNAPSHOT",
                            title=f"Stale Manual RDS Snapshot (>90d): {snap_id}",
                            description=f"Manual snapshot {snap_id} was created on {create_time.strftime('%Y-%m-%d')} (>90 days ago). Delete if no longer needed.",
                            severity="LOW",
                            category="ORPHANED_RESOURCE",
                            resource_type="RDS",
                            resource_id=snap_id,
                            resource_name=snap_id,
                            resource_arn=snap.get("DBSnapshotArn"),
                            region=region,
                            estimated_monthly_savings=monthly_cost,
                            current_monthly_cost=monthly_cost,
                            implementation_effort="low",
                            operational_risk="low",
                            production_safety_score=90,
                            confidence="Observed",
                            remediation_steps=f"Delete stale snapshot: aws rds delete-db-snapshot --db-snapshot-identifier {snap_id} --region {region}",
                            remediation_code=f"aws rds delete-db-snapshot --db-snapshot-identifier {snap_id} --region {region}",
                            raw_data={"allocated_storage_gb": size_gb, "created_at": str(create_time)},
                        ))
        except Exception as e:
            logger.debug("Failed scanning RDS snapshots in %s: %s", region, e)
        return findings

    def _get_avg_metric(self, cw, namespace: str, metric: str, dim_name: str, dim_val: str, start: datetime, end: datetime) -> Optional[float]:
        try:
            response = cw.get_metric_data(
                MetricDataQueries=[{
                    "Id": "m1",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": namespace,
                            "MetricName": metric,
                            "Dimensions": [{"Name": dim_name, "Value": dim_val}],
                        },
                        "Period": 86400,
                        "Stat": "Average",
                    },
                }],
                StartTime=start,
                EndTime=end,
            )
            values = response.get("MetricDataResults", [{}])[0].get("Values", [])
            return (sum(values) / len(values)) if values else None
        except Exception:
            return None

    def _estimate_rds_cost(self, db_class: str, multi_az: bool) -> float:
        rates = {
            "db.t3.micro": 0.017, "db.t3.small": 0.034, "db.t3.medium": 0.068,
            "db.t4g.micro": 0.015, "db.t4g.small": 0.029, "db.t4g.medium": 0.058,
            "db.m5.large": 0.178, "db.m5.xlarge": 0.356, "db.r5.large": 0.24,
        }
        hourly = rates.get(db_class, 0.08)
        if multi_az:
            hourly *= 2.0
        return hourly * 730
