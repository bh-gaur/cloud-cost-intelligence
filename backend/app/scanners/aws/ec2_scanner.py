"""
EC2, EBS, and Elastic IP Cost Optimization & Waste Scanner
Detects idle/stopped instances, unattached EBS volumes, gp2-to-gp3 upgrades, legacy generation upgrades, and unassociated EIPs.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from app.scanners.base import BaseScanner, ScanFinding, ScanContext
from app.scanners.session import AWSSessionManager

logger = logging.getLogger(__name__)

IDLE_CPU_THRESHOLD = 5.0  # percent over 14 days
PREV_GEN_MAP = {
    "t2.nano": ("t4g.nano", 0.0058, 0.0042),
    "t2.micro": ("t4g.micro", 0.0116, 0.0084),
    "t2.small": ("t4g.small", 0.023, 0.0168),
    "t2.medium": ("t4g.medium", 0.0464, 0.0336),
    "t2.large": ("t4g.large", 0.0928, 0.0672),
    "t2.xlarge": ("t4g.xlarge", 0.1856, 0.1344),
    "t2.2xlarge": ("t4g.2xlarge", 0.3712, 0.2688),
    "m4.large": ("m6g.large", 0.10, 0.077),
    "m4.xlarge": ("m6g.xlarge", 0.20, 0.154),
    "m4.2xlarge": ("m6g.2xlarge", 0.40, 0.308),
    "c4.large": ("c6g.large", 0.10, 0.068),
    "c4.xlarge": ("c6g.xlarge", 0.199, 0.136),
    "r4.large": ("r6g.large", 0.133, 0.101),
    "r4.xlarge": ("r6g.xlarge", 0.266, 0.201),
}


class EC2Scanner(BaseScanner):
    def __init__(self, context: ScanContext):
        super().__init__(context)
        self.session = AWSSessionManager.get_session(context.role_arn, context.external_id)

    def scan(self) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        for region in self.context.regions:
            try:
                ec2 = AWSSessionManager.get_client(self.session, "ec2", region)
                cw = AWSSessionManager.get_client(self.session, "cloudwatch", region)

                findings.extend(self._check_idle_instances(ec2, cw, region))
                findings.extend(self._check_unused_ebs(ec2, region))
                findings.extend(self._check_gp2_to_gp3_upgrade(ec2, region))
                findings.extend(self._check_generation_upgrades(ec2, region))
                findings.extend(self._check_unused_eips(ec2, region))
            except Exception as e:
                logger.warning("EC2 scanner encountered an issue in region %s: %s", region, e)
        return findings

    def _check_idle_instances(self, ec2, cw, region: str) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        now = datetime.now(timezone.utc)
        lookback = now - timedelta(days=14)

        try:
            paginator = ec2.get_paginator("describe_instances")
            for page in paginator.paginate(Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped"]}]):
                for res in page.get("Reservations", []):
                    for inst in res.get("Instances", []):
                        iid = inst["InstanceId"]
                        itype = inst["InstanceType"]
                        state = inst["State"]["Name"]
                        tags = self._tag_dict(inst.get("Tags", []))
                        name = tags.get("Name", iid)
                        monthly_cost = self._estimate_ec2_cost(itype)

                        if state == "stopped":
                            # Stopped instances with storage waste
                            findings.append(ScanFinding(
                                rule_id="EC2-STOPPED",
                                title=f"Stopped EC2 Instance Retaining Storage: {name}",
                                description=f"Instance {name} ({itype}) is stopped but still accumulates EBS and elastic IP charges. Terminate or snapshot to stop waste.",
                                severity="LOW",
                                category="IDLE_RESOURCE",
                                resource_type="EC2",
                                resource_id=iid,
                                resource_name=name,
                                resource_arn=f"arn:aws:ec2:{region}:{self.context.aws_account_id}:instance/{iid}",
                                region=region,
                                estimated_monthly_savings=monthly_cost * 0.3,
                                current_monthly_cost=monthly_cost * 0.3,
                                implementation_effort="low",
                                operational_risk="low",
                                production_safety_score=85,
                                confidence="Observed",
                                remediation_steps=f"1. Verify no active dependencies\n2. Create AMI snapshot if data needed\n3. Terminate instance: aws ec2 terminate-instances --instance-ids {iid} --region {region}",
                                remediation_code=f"aws ec2 terminate-instances --instance-ids {iid} --region {region}",
                                resource_tags=tags,
                                raw_data={"instance_type": itype, "state": state},
                            ))
                            continue

                        # Running instances: evaluate CPU utilization
                        avg_cpu = self._get_avg_cpu(cw, iid, lookback, now)
                        if avg_cpu is not None and avg_cpu < IDLE_CPU_THRESHOLD:
                            savings = monthly_cost * 0.7
                            findings.append(ScanFinding(
                                rule_id="EC2-IDLE",
                                title=f"Idle EC2 Instance Detected: {name}",
                                description=f"Instance {name} ({itype}) averaged {avg_cpu:.1f}% CPU over the past 14 days (< {IDLE_CPU_THRESHOLD}% threshold). Stop or downsize.",
                                severity="HIGH" if monthly_cost > 100 else "MEDIUM",
                                category="IDLE_RESOURCE",
                                resource_type="EC2",
                                resource_id=iid,
                                resource_name=name,
                                resource_arn=f"arn:aws:ec2:{region}:{self.context.aws_account_id}:instance/{iid}",
                                region=region,
                                estimated_monthly_savings=savings,
                                current_monthly_cost=monthly_cost,
                                implementation_effort="low",
                                operational_risk="medium",
                                production_safety_score=75,
                                confidence="Observed",
                                remediation_steps=f"1. Validate workload with application owner\n2. Stop instance during idle periods or downsize: aws ec2 stop-instances --instance-ids {iid} --region {region}",
                                remediation_code=f"aws ec2 stop-instances --instance-ids {iid} --region {region}",
                                resource_tags=tags,
                                raw_data={"instance_type": itype, "avg_cpu_14d": avg_cpu},
                            ))
        except Exception as e:
            logger.debug("Failed checking idle instances in %s: %s", region, e)
        return findings

    def _check_unused_ebs(self, ec2, region: str) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        try:
            paginator = ec2.get_paginator("describe_volumes")
            for page in paginator.paginate(Filters=[{"Name": "status", "Values": ["available"]}]):
                for vol in page.get("Volumes", []):
                    vid = vol["VolumeId"]
                    size_gb = vol["Size"]
                    vol_type = vol["VolumeType"]
                    tags = self._tag_dict(vol.get("Tags", []))
                    name = tags.get("Name", vid)
                    monthly_cost = self._estimate_ebs_cost(size_gb, vol_type)

                    findings.append(ScanFinding(
                        rule_id="EBS-UNUSED",
                        title=f"Unattached Unused EBS Volume: {name}",
                        description=f"EBS volume {name} ({size_gb}GB {vol_type}) is unattached and accumulating charges of ${monthly_cost:.2f}/mo.",
                        severity="MEDIUM" if monthly_cost > 50 else "LOW",
                        category="ORPHANED_RESOURCE",
                        resource_type="EBS",
                        resource_id=vid,
                        resource_name=name,
                        resource_arn=f"arn:aws:ec2:{region}:{self.context.aws_account_id}:volume/{vid}",
                        region=region,
                        estimated_monthly_savings=monthly_cost,
                        current_monthly_cost=monthly_cost,
                        implementation_effort="low",
                        operational_risk="low",
                        production_safety_score=95,
                        confidence="Observed",
                        remediation_steps=f"1. Create snapshot backup: aws ec2 create-snapshot --volume-id {vid} --region {region}\n2. Delete volume: aws ec2 delete-volume --volume-id {vid} --region {region}",
                        remediation_code=f"aws ec2 create-snapshot --volume-id {vid} --description 'Backup prior to deletion' --region {region} && aws ec2 delete-volume --volume-id {vid} --region {region}",
                        resource_tags=tags,
                        raw_data={"size_gb": size_gb, "volume_type": vol_type},
                    ))
        except Exception as e:
            logger.debug("Failed checking unused EBS in %s: %s", region, e)
        return findings

    def _check_gp2_to_gp3_upgrade(self, ec2, region: str) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        try:
            paginator = ec2.get_paginator("describe_volumes")
            for page in paginator.paginate(Filters=[{"Name": "volume-type", "Values": ["gp2"]}]):
                for vol in page.get("Volumes", []):
                    vid = vol["VolumeId"]
                    size_gb = vol["Size"]
                    tags = self._tag_dict(vol.get("Tags", []))
                    name = tags.get("Name", vid)

                    current_cost = size_gb * 0.10
                    gp3_cost = size_gb * 0.08
                    savings = current_cost - gp3_cost

                    if savings >= 1.0:
                        findings.append(ScanFinding(
                            rule_id="EBS-GP2-TO-GP3",
                            title=f"Upgrade gp2 EBS Volume to gp3: {name}",
                            description=f"Volume {name} ({size_gb}GB) uses previous-gen gp2 storage. Upgrading to gp3 saves 20% while providing baseline 3,000 IOPS.",
                            severity="LOW",
                            category="MODERNIZATION",
                            resource_type="EBS",
                            resource_id=vid,
                            resource_name=name,
                            resource_arn=f"arn:aws:ec2:{region}:{self.context.aws_account_id}:volume/{vid}",
                            region=region,
                            estimated_monthly_savings=savings,
                            current_monthly_cost=current_cost,
                            implementation_effort="low",
                            operational_risk="low",
                            production_safety_score=98,
                            confidence="Estimated",
                            remediation_steps=f"Execute zero-downtime volume modification: aws ec2 modify-volume --volume-id {vid} --volume-type gp3 --region {region}",
                            remediation_code=f"aws ec2 modify-volume --volume-id {vid} --volume-type gp3 --region {region}",
                            resource_tags=tags,
                            raw_data={"size_gb": size_gb, "current_type": "gp2", "target_type": "gp3"},
                        ))
        except Exception as e:
            logger.debug("Failed checking gp2 to gp3 in %s: %s", region, e)
        return findings

    def _check_generation_upgrades(self, ec2, region: str) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        try:
            paginator = ec2.get_paginator("describe_instances")
            for page in paginator.paginate(Filters=[{"Name": "instance-state-name", "Values": ["running"]}]):
                for res in page.get("Reservations", []):
                    for inst in res.get("Instances", []):
                        iid = inst["InstanceId"]
                        itype = inst["InstanceType"]
                        if itype in PREV_GEN_MAP:
                            target_type, curr_hr, next_hr = PREV_GEN_MAP[itype]
                            curr_mo = curr_hr * 730
                            next_mo = next_hr * 730
                            savings = curr_mo - next_mo
                            tags = self._tag_dict(inst.get("Tags", []))
                            name = tags.get("Name", iid)

                            findings.append(ScanFinding(
                                rule_id="EC2-GEN-UPGRADE",
                                title=f"Modernize Previous-Gen EC2 Instance: {name}",
                                description=f"Instance {name} ({itype}) is on older generation hardware. Upgrading to {target_type} provides ~20-30% higher performance at ${savings:.2f}/mo lower cost.",
                                severity="LOW",
                                category="MODERNIZATION",
                                resource_type="EC2",
                                resource_id=iid,
                                resource_name=name,
                                resource_arn=f"arn:aws:ec2:{region}:{self.context.aws_account_id}:instance/{iid}",
                                region=region,
                                estimated_monthly_savings=savings,
                                current_monthly_cost=curr_mo,
                                implementation_effort="medium",
                                operational_risk="medium",
                                production_safety_score=80,
                                confidence="Estimated",
                                remediation_steps=f"1. Stop instance: aws ec2 stop-instances --instance-ids {iid} --region {region}\n2. Modify type: aws ec2 modify-instance-attribute --instance-id {iid} --instance-type {target_type} --region {region}\n3. Start instance: aws ec2 start-instances --instance-ids {iid} --region {region}",
                                remediation_code=f"aws ec2 modify-instance-attribute --instance-id {iid} --instance-type {target_type} --region {region}",
                                resource_tags=tags,
                                raw_data={"current_type": itype, "target_type": target_type},
                            ))
        except Exception as e:
            logger.debug("Failed checking generation upgrades in %s: %s", region, e)
        return findings

    def _check_unused_eips(self, ec2, region: str) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        try:
            addresses = ec2.describe_addresses().get("Addresses", [])
            for addr in addresses:
                if "AssociationId" not in addr and "InstanceId" not in addr:
                    eip = addr.get("PublicIp", "unknown")
                    alloc_id = addr.get("AllocationId", eip)
                    monthly_cost = 3.60  # $0.005/hr * 720hr = $3.60/month

                    findings.append(ScanFinding(
                        rule_id="EIP-UNATTACHED",
                        title=f"Unassociated Elastic IP Address: {eip}",
                        description=f"Elastic IP {eip} is allocated but not attached to any running resource, accumulating $3.60/month AWS charge.",
                        severity="LOW",
                        category="ORPHANED_RESOURCE",
                        resource_type="EIP",
                        resource_id=alloc_id,
                        resource_name=eip,
                        resource_arn=f"arn:aws:ec2:{region}:{self.context.aws_account_id}:elastic-ip/{alloc_id}",
                        region=region,
                        estimated_monthly_savings=monthly_cost,
                        current_monthly_cost=monthly_cost,
                        implementation_effort="low",
                        operational_risk="low",
                        production_safety_score=95,
                        confidence="Observed",
                        remediation_steps=f"Release Elastic IP: aws ec2 release-address --allocation-id {alloc_id} --region {region}",
                        remediation_code=f"aws ec2 release-address --allocation-id {alloc_id} --region {region}",
                        raw_data={"allocation_id": alloc_id, "public_ip": eip},
                    ))
        except Exception as e:
            logger.debug("Failed checking unused EIPs in %s: %s", region, e)
        return findings

    def _get_avg_cpu(self, cw, instance_id: str, start: datetime, end: datetime) -> Optional[float]:
        try:
            response = cw.get_metric_data(
                MetricDataQueries=[{
                    "Id": "m1",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/EC2",
                            "MetricName": "CPUUtilization",
                            "Dimensions": [{"Name": "InstanceId", "Value": instance_id}],
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

    def _estimate_ec2_cost(self, instance_type: str) -> float:
        # Standard hourly pricing reference map
        rates = {
            "t2.nano": 0.0058, "t2.micro": 0.0116, "t2.small": 0.023, "t2.medium": 0.0464,
            "t3.nano": 0.0052, "t3.micro": 0.0104, "t3.small": 0.0208, "t3.medium": 0.0416,
            "t4g.nano": 0.0042, "t4g.micro": 0.0084, "t4g.small": 0.0168, "t4g.medium": 0.0336,
            "m5.large": 0.096, "m5.xlarge": 0.192, "c5.large": 0.085, "c5.xlarge": 0.17,
        }
        hourly = rates.get(instance_type, 0.05)
        return hourly * 730

    def _estimate_ebs_cost(self, size_gb: int, vol_type: str) -> float:
        rates = {"gp3": 0.08, "gp2": 0.10, "io1": 0.125, "io2": 0.125, "st1": 0.045, "sc1": 0.015}
        rate = rates.get(vol_type, 0.10)
        return size_gb * rate
