"""
Application Configuration and Settings
Loaded from environment variables and .env file with zero external dependencies.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


def _load_env_file(dotenv_path: Path):
    """Simple parser for .env files without extra dependencies."""
    if not dotenv_path.is_file():
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val


# Load from repo root or backend folder
_root_env = Path(__file__).resolve().parent.parent.parent.parent / ".env"
_backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
_load_env_file(_root_env)
_load_env_file(_backend_env)


class Settings:
    """Dynamic application settings that reflect live environment & .env state."""

    @property
    def APP_NAME(self) -> str:
        return os.getenv("APP_NAME", "AWS Cost Intelligence")

    @property
    def PRODUCT_NAME(self) -> str:
        return os.getenv("PRODUCT_NAME", "cloud-cost-intelligence")

    @property
    def ENVIRONMENT(self) -> str:
        return os.getenv("ENVIRONMENT", "development")

    @property
    def DEBUG(self) -> bool:
        return os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    @property
    def DEMO_MODE(self) -> bool:
        return os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")

    @property
    def DATABASE_URL(self) -> str:
        url = os.getenv("DATABASE_URL")
        backend_dir = Path(__file__).resolve().parent.parent.parent
        if not url:
            return f"sqlite:///{backend_dir / 'cloud_cost.db'}"
        if url.startswith("sqlite:///./") or url == "sqlite:///cloud_cost.db":
            return f"sqlite:///{backend_dir / 'cloud_cost.db'}"
        return url

    @property
    def SECRET_KEY(self) -> str:
        return os.getenv("SECRET_KEY", "finops-cost-intelligence-production-secure-key-2026")

    @property
    def JWT_ALGORITHM(self) -> str:
        return os.getenv("JWT_ALGORITHM", "HS256")

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        return int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    @property
    def GOOGLE_CLIENT_ID(self) -> str:
        return os.getenv("GOOGLE_CLIENT_ID", "")

    @property
    def GOOGLE_CLIENT_SECRET(self) -> str:
        return os.getenv("GOOGLE_CLIENT_SECRET", "")

    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        return os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/callback")

    @property
    def CORS_ORIGINS(self) -> str:
        return os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def AWS_DEFAULT_REGION(self) -> str:
        return os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    @property
    def AWS_ROLE_ARN(self) -> Optional[str]:
        return None

    @property
    def AWS_ROLE_EXTERNAL_ID(self) -> Optional[str]:
        return None

    @property
    def AWS_ACCESS_KEY_ID(self) -> Optional[str]:
        return os.getenv("AWS_ACCESS_KEY_ID")

    @property
    def AWS_SECRET_ACCESS_KEY(self) -> Optional[str]:
        return os.getenv("AWS_SECRET_ACCESS_KEY")

    @property
    def AWS_SESSION_TOKEN(self) -> Optional[str]:
        return os.getenv("AWS_SESSION_TOKEN")

    @property
    def SMTP_HOST(self) -> Optional[str]:
        _load_env_file(_root_env)
        return os.getenv("SMTP_HOST")

    @property
    def SMTP_PORT(self) -> int:
        return int(os.getenv("SMTP_PORT", "587"))

    @property
    def SMTP_USERNAME(self) -> Optional[str]:
        _load_env_file(_root_env)
        return os.getenv("SMTP_USERNAME")

    @property
    def SMTP_PASSWORD(self) -> Optional[str]:
        _load_env_file(_root_env)
        return os.getenv("SMTP_PASSWORD")

    @property
    def SMTP_FROM(self) -> str:
        _load_env_file(_root_env)
        return os.getenv("SMTP_FROM", "AWS Cost Intelligence <finops-alerts@example.com>")

    @property
    def EMAIL_RECIPIENTS(self) -> Optional[str]:
        _load_env_file(_root_env)
        return os.getenv("EMAIL_RECIPIENTS")

    @property
    def SLACK_WEBHOOK_URL(self) -> Optional[str]:
        _load_env_file(_root_env)
        return os.getenv("SLACK_WEBHOOK_URL")

    @property
    def GCHAT_WEBHOOK_URL(self) -> Optional[str]:
        return os.getenv("GCHAT_WEBHOOK_URL")

    @property
    def TEAMS_WEBHOOK_URL(self) -> Optional[str]:
        return os.getenv("TEAMS_WEBHOOK_URL")

    @property
    def REPORT_RETENTION_DAYS(self) -> int:
        return int(os.getenv("REPORT_RETENTION_DAYS", "90"))

    @property
    def REPORT_OUTPUT_DIR(self) -> str:
        return os.getenv(
            "REPORT_OUTPUT_DIR",
            str(Path(__file__).resolve().parent.parent.parent / "reports"),
        )


settings = Settings()


