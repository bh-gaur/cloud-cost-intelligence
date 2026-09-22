# Contributing to AWS Cost Intelligence

Thank you for your interest in contributing to the AWS Cost Intelligence platform (`cloud-cost-intelligence`)!

## Code of Conduct

Please maintain an inclusive, professional, and respectful environment for all contributors.

## Development Workflow

1. Fork and clone the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. Install dependencies:
   ```bash
   make install
   ```
4. Run tests:
   ```bash
   make test
   ```
5. Apply linting and formatting:
   ```bash
   make lint
   make format
   ```
6. Commit your changes following conventional commits:
   ```bash
   git commit -m "feat(optimization): add Aurora Serverless v2 rightsizing rule"
   ```
7. Push to your branch and open a Pull Request.

## Coding Standards

### Backend (Python / FastAPI)
- Strict type hinting across all modules.
- Use `Decimal` / `Numeric` for monetary amounts. Never store or sum monetary values using `float`.
- API endpoints must return the standardized `ApiResponse` envelope (`success`, `data`, `error`, `meta`).
- Optimization rules must inherit from `BaseOptimizationRule` and output `Recommendation`.
- Never log passwords, tokens, role ARNs, external IDs, or webhook URLs.

### Frontend (React / TypeScript)
- Use functional components with TypeScript interfaces.
- Manage server state exclusively using TanStack Query.
- Use deterministic colors from `src/constants/serviceColors.ts` for all service representations.
- Ensure all interactive elements have keyboard navigation and ARIA attributes.
- Support both Light and Dark mode using Tailwind CSS utility classes.

### Security
- AWS permissions must adhere to least privilege read-only access.
- Any new notification integration or report generator must validate against path traversal and secret exposure.

