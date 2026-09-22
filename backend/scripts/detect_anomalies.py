#!/usr/bin/env python3
"""
detect_anomalies.py
CLI tool to scan historical cost records and detect spend anomalies and budget threshold breaches.

Usage:
    python detect_anomalies.py
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.alerts.detector import AnomalyDetector
from app.providers.factory import get_cloud_provider


def main():
    print("[*] Running AWS Cost Anomaly Detector & Budget Tracker...")
    provider = get_cloud_provider()
    detector = AnomalyDetector(provider)
    db = SessionLocal()

    try:
        events = detector.detect_daily_anomalies(db)
        print(f"[✓] Daily anomaly scan complete. Detected {len(events)} anomalies:")
        for e in events:
            print(f"    - [{e.severity}] {e.title}: {e.message}")

        budgets = detector.sync_budgets(db)
        print(f"[✓] Synchronized {len(budgets)} AWS Budgets:")
        for b in budgets:
            print(f"    - {b.budget_name}: {b.percentage_consumed:.1f}% consumed (${b.current_spend:,.2f} of ${b.budget_limit:,.2f}) [{b.status}]")
    finally:
        db.close()


if __name__ == "__main__":
    main()

