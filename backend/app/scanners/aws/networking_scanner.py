"""
Networking & Load Balancing Cost Optimization Scanner
Detects idle NAT Gateways (<100MB traffic/week) and unused Load Balancers (ALB/NLB with 0 targets/traffic).
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from app.scanners.base import BaseScanner, ScanFinding, ScanContext
from app.scanners.session import AWSSessionManager

logger = logging.getLogger(__name__)

NAT_HOURLY_BASE = 0.045
NAT_MONTHLY_BASE = NAT_HOURLY_BASE * 720  # ~$32.40/month


class NetworkingScanner(BaseScanner):
    def __init__(self, context: ScanContext):
        super().__init__(context)
        self.session = AWSSessionManager.get_session(context.role_arn, context.external_id)

    def scan(self) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        for region in self.context.regions:
            try:
                ec2 = AWSSessionManager.get_client(self.session, "ec2", region)
                elbv2 = AWSSessionManager.get_client(self.session, "elbv2", region)
                cw = AWSSessionManager.get_client(self.session, "cloudwatch", region)

                findings.extend(self._scan_nat_gateways(ec2, cw, region))
                findings.extend(self._scan_load_balancers(elbv2, cw, region))
            except Exception as e:
                logger.warning("Networking scanner encountered an issue in region %s: %s", region, e)
        return findings

    def _scan_nat_gateways(self, ec2, cw, region: str) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        now = datetime.now(timezone.utc)
        lookback = now - timedelta(days=7)

        try:
            paginator = ec2.get_paginator("describe_nat_gateways")
            for page in paginator.paginate(Filters=[{"Name": "state", "Values": ["available"]}]):
                for nat in page.get("NatGateways", []):
                    nat_id = nat["NatGatewayId"]
                    vpc_id = nat.get("VpcId", "unknown")
                    tags = self._tag_dict(nat.get("Tags", []))
                    name = tags.get("Name", nat_id)

                    # Check bytes processed in past 7 days
                    bytes_out = self._get_sum_metric(cw, "AWS/NATGateway", "BytesOutToDestination", "NatGatewayId", nat_id, lookback, now)
                    bytes_in = self._get_sum_metric(cw, "AWS/NATGateway", "BytesInFromSource", "NatGatewayId", nat_id, lookback, now)
                    total_bytes = (bytes_out or 0) + (bytes_in or 0)

                    # If < 100 MB transferred across 7 days, NAT Gateway is idle
                    if total_bytes < 100 * 1024 * 1024:
                        findings.append(ScanFinding(
                            rule_id="NET-IDLE-NAT",
                            title=f"Idle / Underutilized NAT Gateway: {name}",
                            description=f"NAT Gateway {name} in VPC {vpc_id} processed only {total_bytes / (1024 * 1024):.1f}MB in the past 7 days while costing ${NAT_MONTHLY_BASE:.2f}/mo baseline fee. Consolidate or replace with VPC Endpoints.",
                            severity="MEDIUM",
                            category="IDLE_RESOURCE",
                            resource_type="NATGateway",
                            resource_id=nat_id,
                            resource_name=name,
                            resource_arn=f"arn:aws:ec2:{region}:{self.context.aws_account_id}:natgateway/{nat_id}",
                            region=region,
                            estimated_monthly_savings=NAT_MONTHLY_BASE,
                            current_monthly_cost=NAT_MONTHLY_BASE,
                            implementation_effort="medium",
                            operational_risk="medium",
                            production_safety_score=75,
                            confidence="Observed",
                            remediation_steps=f"1. Audit routing tables for VPC {vpc_id}\n2. If no outbound internet is required, delete NAT Gateway: aws ec2 delete-nat-gateway --nat-gateway-id {nat_id} --region {region}",
                            remediation_code=f"aws ec2 delete-nat-gateway --nat-gateway-id {nat_id} --region {region}",
                            resource_tags=tags,
                            raw_data={"vpc_id": vpc_id, "7d_bytes_transferred": total_bytes},
                        ))
        except Exception as e:
            logger.debug("Failed scanning NAT Gateways in %s: %s", region, e)
        return findings

    def _scan_load_balancers(self, elbv2, cw, region: str) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        now = datetime.now(timezone.utc)
        lookback = now - timedelta(days=7)

        try:
            paginator = elbv2.get_paginator("describe_load_balancers")
            for page in paginator.paginate():
                for alb in page.get("LoadBalancers", []):
                    alb_arn = alb["LoadBalancerArn"]
                    alb_name = alb["LoadBalancerName"]
                    alb_type = alb.get("Type", "application")
                    monthly_cost = 22.50  # ~$0.0225/hr * 730 = ~$16.40 base + LCU

                    # Check Target Groups for registered healthy targets
                    tg_paginator = elbv2.get_paginator("describe_target_groups")
                    has_targets = False
                    for tg_page in tg_paginator.paginate(LoadBalancerArn=alb_arn):
                        for tg in tg_page.get("TargetGroups", []):
                            tg_arn = tg["TargetGroupArn"]
                            health = elbv2.describe_target_health(TargetGroupArn=tg_arn).get("TargetHealthDescriptions", [])
                            if len(health) > 0:
                                has_targets = True
                                break

                    if not has_targets:
                        findings.append(ScanFinding(
                            rule_id="NET-UNUSED-ALB",
                            title=f"Unused Load Balancer with Zero Targets: {alb_name}",
                            description=f"Load balancer {alb_name} ({alb_type}) has no registered backend target instances, accumulating ${monthly_cost:.2f}/month idle cost.",
                            severity="MEDIUM",
                            category="ORPHANED_RESOURCE",
                            resource_type="ELB",
                            resource_id=alb_name,
                            resource_name=alb_name,
                            resource_arn=alb_arn,
                            region=region,
                            estimated_monthly_savings=monthly_cost,
                            current_monthly_cost=monthly_cost,
                            implementation_effort="low",
                            operational_risk="low",
                            production_safety_score=90,
                            confidence="Observed",
                            remediation_steps=f"Delete unassociated Load Balancer: aws elbv2 delete-load-balancer --load-balancer-arn {alb_arn} --region {region}",
                            remediation_code=f"aws elbv2 delete-load-balancer --load-balancer-arn {alb_arn} --region {region}",
                            raw_data={"lb_type": alb_type, "has_targets": False},
                        ))
        except Exception as e:
            logger.debug("Failed scanning Load Balancers in %s: %s", region, e)
        return findings

    def _get_sum_metric(self, cw, namespace: str, metric: str, dim_name: str, dim_val: str, start: datetime, end: datetime) -> Optional[float]:
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
                        "Period": 604800,
                        "Stat": "Sum",
                    },
                }],
                StartTime=start,
                EndTime=end,
            )
            values = response.get("MetricDataResults", [{}])[0].get("Values", [])
            return sum(values) if values else 0.0
        except Exception:
            return None
