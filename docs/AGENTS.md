# Agent & Developer Guidelines (AGENTS.md)

Welcome, AI agent or human engineer! This document establishes mandatory conventions, design patterns, rules, and commands for the **AWS Cost Intelligence** platform (`cloud-cost-intelligence`).

---

## 1. Core Architecture Principles

1. **Provider Abstraction**:
   - Never import `boto3` outside `backend/app/providers/aws/`.
   - All cloud operations must implement `CloudProvider` in `backend/app/providers/base.py`.
   - For demo or development environments, `MockAWSProvider` (`backend/app/providers/mock/`) must supply rich, deterministic data without external calls.
   - When `DEMO_MODE=true`, the UI must display a prominent `DEMO DATA` badge.
2. **Strict Financial Precision**:
   - NEVER use `float` for money in Python or SQL.
   - Use `Decimal` in Python and `NUMERIC(18, 4)` in PostgreSQL.
   - Round to 2 decimal places only at the presentation layer (UI components, CSV/HTML report templates).
3. **No Fake Operations**:
   - Never return "Success" if an external provider or database call was not verified.
   - Connection test endpoints must actually exercise the adapter and return explicit errors upon failure.
4. **Deterministic Service Colors**:
   - Never hardcode color hex codes in individual frontend components.
   - Always resolve service colors through `getServiceColor(serviceName)` in `frontend/src/constants/serviceColors.ts`.
5. **Strict Server-Side Authorization & Multi-Tenancy**:
   - NEVER trust frontend-supplied `organization_id`, `role`, or permissions.
   - All protected endpoints MUST evaluate `TenantContext` (`get_tenant_context`) and check server-side permissions (`RequirePermission(PERM_NAME)`).
   - Enforce 5 organization roles: `OWNER`, `ADMIN`, `FINOPS_MANAGER`, `ANALYST`, `VIEWER`.
   - Protect against IDOR by checking resource organization ownership (`resource.organization_id == tenant_ctx.organization_id`).
   - Enforce Owner Protection (prevent removing last `OWNER`) and Role Escalation Protection (prevent self-escalation or promoting users above caller's role level).
6. **Multi-Currency Telemetry & Live Exchange Rates**:
   - `CurrencyContext` (`frontend/src/context/CurrencyContext.tsx`) manages active user currency (`USD` vs `INR`).
   - Fetches live USD/INR exchange rates from `https://open.er-api.com/v6/latest/USD`, with caching in `localStorage` and fallback rate `83.5`.
   - All monetary amounts displayed across frontend tables, KPI cards, alerts, and reports must be formatted via `formatCurrency()` from `frontend/src/utils/formatters.ts`.
7. **Defensive HTTP Security & CORS Policies**:
   - Middleware in `backend/app/main.py` injects mandatory HTTP security headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, `HSTS`).
   - CORS is strictly configured to explicitly allowed origins, methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`), and headers (`Authorization`, `Content-Type`, `X-Organization-ID`).
8. **Enterprise Password Security**:
   - `validate_password_strength()` in `backend/app/auth/security.py` enforces passwords with minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character.
9. **Production Demo Mode & Route Security Guards**:
   - `PublicOnlyRoute` in `frontend/src/App.tsx` guards `/login` and `/register` to prevent auth flickering for logged-in users.
   - Demo access buttons on `/login` are restricted to environments where backend reports `DEMO_MODE=true` or explicit `?demo=true` URL parameter. One-click demo triggers immediate authentication.

---

## 2. Project Directory Map

```
cloud-cost-intelligence/
├── frontend/                     # React 18 + TypeScript + Vite + Tailwind UI
│   ├── src/
│   │   ├── api/                  # Modular Axios/Fetch clients
│   │   ├── components/           # Common UI primitives & layouts
│   │   ├── constants/            # Service color registry & navigation configs
│   │   ├── pages/                # Route view components
│   │   ├── types/                # Shared TypeScript contracts
│   │   └── utils/                # Formatting & math utilities
├── backend/                      # FastAPI Python Application
│   ├── app/
│   │   ├── api/v1/               # Versioned REST API routes
│   │   ├── auth/                 # JWT & RBAC security utilities
│   │   ├── config/               # Settings loaded via Pydantic BaseSettings
│   │   ├── database/             # SQLAlchemy engine & session factory
│   │   ├── models/               # SQLAlchemy ORM entities
│   │   ├── schemas/              # Pydantic v2 request/response models
│   │   ├── providers/            # Base interface, AWS Boto3, and Mock provider
│   │   ├── optimization/         # Rule engine and modular FinOps rules
│   │   ├── notifications/        # Slack, Teams, GChat, SMTP dispatchers
│   │   └── reports/              # CSV, JSON, HTML report generators
│   ├── scripts/                  # Standalone CLI tools
│   └── tests/                    # Pytest test suite
├── database/                     # Migrations & seed scripts
└── docs/                         # Detailed system documentation
```

---

## 3. How to Extend the Platform

### A. How to Add a New AWS Service to the Dashboard
1. Add the service name to the known mapping in `frontend/src/constants/serviceColors.ts` with its assigned color.
2. If the service supports specific resource utilization metrics (e.g. Memory for Lambda, IOPS for EBS), update `backend/app/providers/aws/` with relevant describe calls.
3. Update `backend/app/providers/mock/provider.py` to generate sample historical data for this service during demo runs.

### B. How to Add a New Optimization Rule
1. Create a new file in `backend/app/optimization/rules/<rule_name>.py`.
2. Subclass `BaseOptimizationRule` and implement:
   ```python
   class MyOptimizationRule(BaseOptimizationRule):
       rule_id = "OPT-012"
       name = "Aurora Serverless Scaling Optimization"
       service = "Amazon Relational Database Service"
       
       def evaluate(self, account_id: str, region: str, provider_data: Any) -> List[Recommendation]:
           ...
   ```
3. Register the rule in `backend/app/optimization/engine.py`.
4. Add a unit test in `backend/tests/test_optimization.py`.

### C. How to Add a New Notification Channel
1. Create `backend/app/notifications/<channel_name>.py`.
2. Implement `NotificationProvider` interface (`send`, `validate_configuration`, `health_check`).
3. Register the provider in `backend/app/notifications/service.py`.
4. Add configuration fields in `backend/app/config/settings.py` and `.env.example`.

### D. How to Add a New Report Format
1. Add a generator class under `backend/app/reports/generators/<format>_generator.py`.
2. Subclass `BaseReportGenerator` and implement `generate(self, report_data: ReportData) -> bytes`.
3. Register the format in `backend/app/reports/service.py`.

---

## 4. Key Developer Commands

```bash
# Setup & Installation
make install

# Start Backend (Port 8000)
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Frontend (Port 5173)
cd frontend && npm run dev

# Run Backend Tests
cd backend && pytest -v tests/

# Run Frontend Tests
cd frontend && npm run test -- --run

# Seed Demo Data
cd backend && python scripts/seed_demo_data.py

# Fetch Costs (Standalone CLI)
cd backend && python scripts/fetch_costs.py --provider mock --start-date 2026-09-01 --end-date 2026-09-12

# Generate Report (Standalone CLI)
cd backend && python scripts/generate_report.py --format html --output-dir reports/html/

# Send Report (Standalone CLI)
cd backend && python scripts/send_report.py --channel slack --dry-run
```

