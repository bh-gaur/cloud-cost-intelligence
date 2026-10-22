# AWS Cost Intelligence - Backend Service

FastAPI-powered asynchronous backend service delivering FinOps cost aggregation, AWS Cost Explorer integration, optimization rules, multi-format report generation, and multi-channel alerting.

## Key Directories

- `app/api/v1/`: Versioned REST API endpoints.
- `app/providers/`: Cloud Provider Abstraction (`AWSProvider` & `MockAWSProvider`).
- `app/optimization/`: Rule-based FinOps optimization engine with 11+ rules.
- `app/reports/`: Executive CSV and PDF report generators.
- `app/notifications/`: Multi-channel dispatchers (Email, Slack, Webhook).
- `scripts/`: Standalone CLI management scripts.

## Running Locally

Activate the project's virtual environment first:

```bash
# Navigate to the backend directory
cd backend

# Activate virtual environment
source .venv/bin/activate

# Seed initial demo dataset
python scripts/seed_demo_data.py

# Launch development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Alternatively, you can run directly without activating:

```bash
# Using the virtualenv Python directly
.venv/bin/python scripts/seed_demo_data.py
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using uv (if installed)
uv run python scripts/seed_demo_data.py
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

