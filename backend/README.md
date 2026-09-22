# AWS Cost Intelligence - Backend Service

FastAPI-powered asynchronous backend service delivering FinOps cost aggregation, AWS Cost Explorer integration, optimization rules, multi-format report generation, and multi-channel alerting.

## Key Directories

- `app/api/v1/`: Versioned REST API endpoints.
- `app/providers/`: Cloud Provider Abstraction (`AWSProvider` & `MockAWSProvider`).
- `app/optimization/`: Rule-based FinOps optimization engine with 11+ rules.
- `app/reports/`: CSV, JSON, and print-ready HTML report generators.
- `app/notifications/`: Multi-channel dispatchers (Email, Slack, Teams, Google Chat).
- `scripts/`: Standalone CLI management scripts.

## Running Locally

```bash
# Seed initial demo dataset
python scripts/seed_demo_data.py

# Launch development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

