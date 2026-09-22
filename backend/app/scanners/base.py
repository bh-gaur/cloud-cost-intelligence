"""
Base Scanner & Findings Architecture
Defines standardized ScanFinding, ScanContext, and BaseScanner for deep AWS resource inspection.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScanFinding:
    rule_id: str
    title: str
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str  # IDLE_RESOURCE, RIGHTSIZING, STORAGE_OPTIMIZATION, MODERNIZATION, RESERVATIONS, ORPHANED_RESOURCE
    resource_type: str
    resource_id: str
    resource_name: Optional[str] = None
    resource_arn: Optional[str] = None
    region: Optional[str] = None
    estimated_monthly_savings: float = 0.0
    current_monthly_cost: float = 0.0
    implementation_effort: str = "medium"  # low, medium, high
    operational_risk: str = "low"  # low, medium, high
    production_safety_score: int = 80  # 0 to 100
    confidence: str = "Estimated"  # Observed, Estimated, Potential
    remediation_steps: Optional[str] = None
    remediation_code: Optional[str] = None
    resource_tags: Dict[str, str] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        key = f"{self.rule_id}:{self.resource_type}:{self.resource_id}:{self.region}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "category": self.category,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "resource_arn": self.resource_arn,
            "region": self.region,
            "estimated_monthly_savings": self.estimated_monthly_savings,
            "current_monthly_cost": self.current_monthly_cost,
            "implementation_effort": self.implementation_effort,
            "operational_risk": self.operational_risk,
            "production_safety_score": self.production_safety_score,
            "confidence": self.confidence,
            "remediation_steps": self.remediation_steps,
            "remediation_code": self.remediation_code,
            "resource_tags": self.resource_tags,
            "fingerprint": self.fingerprint(),
        }


@dataclass
class ScanContext:
    organization_id: str
    aws_account_id: str
    aws_account_name: str
    role_arn: Optional[str] = None
    external_id: Optional[str] = None
    regions: List[str] = field(default_factory=lambda: ["us-east-1", "us-east-2", "us-west-2", "ap-south-1", "eu-west-1"])
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseScanner(ABC):
    def __init__(self, context: ScanContext):
        self.context = context

    @abstractmethod
    def scan(self) -> List[ScanFinding]:
        """Executes deep scanning against the context's AWS account."""
        pass

    def _tag_dict(self, tags: Optional[List[Dict[str, str]]]) -> Dict[str, str]:
        if not tags:
            return {}
        return {t.get("Key", ""): t.get("Value", "") for t in tags if "Key" in t}
