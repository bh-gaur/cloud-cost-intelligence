"""
JSON Report Generator
Serializes complete report model into formatted JSON.
"""

import json
from decimal import Decimal
from typing import Any, Dict


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return super().default(obj)


class JSONReportGenerator:
    def generate(self, data: Dict[str, Any]) -> str:
        """Serializes dictionary payload into pretty JSON string."""
        return json.dumps(data, indent=2, cls=DecimalEncoder)

