#!/usr/bin/env python3
"""
generate_optimizations.py
CLI tool to evaluate all 11+ FinOps optimization rules and write recommendations into database.

Usage:
    python generate_optimizations.py
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.optimization.engine import OptimizationEngine
from app.providers.factory import get_cloud_provider


def main():
    print("[*] Executing FinOps Cost Optimization Rule Engine...")
    provider = get_cloud_provider()
    engine = OptimizationEngine(provider)
    db = SessionLocal()

    try:
        recs = engine.run_all(db)
        summary = OptimizationEngine.get_summary(db)

        print(f"[✓] Engine evaluation complete. Generated {len(recs)} recommendations.")
        print(f"    Total Potential Monthly Savings: ${summary['total_monthly_savings']:,.2f}")
        print(f"    Total Potential Annual Savings:  ${summary['total_annual_savings']:,.2f}")
        print("\n    Breakdown by Confidence:")
        for conf, amt in summary["by_confidence"].items():
            print(f"      - {conf}: ${amt:,.2f}/mo")

        print("\n    Top Opportunities:")
        for r in sorted(recs, key=lambda x: x.estimated_monthly_savings, reverse=True)[:5]:
            print(f"      - [{r.priority}] {r.rule_name} on {r.resource_id}: ${r.estimated_monthly_savings:,.2f}/mo ({r.confidence})")
    finally:
        db.close()


if __name__ == "__main__":
    main()

