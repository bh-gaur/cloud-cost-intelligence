"""
Pytest Configuration & Fixtures
"""

import os
os.environ["DEMO_MODE"] = "true"
import sys
from datetime import date, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.user import Role, User
from app.auth.security import hash_password, create_access_token
from app.providers.mock.provider import MockAWSProvider
from app.services.cost_service import CostService
from app.optimization.engine import OptimizationEngine

from sqlalchemy.pool import StaticPool

# In-memory SQLite with StaticPool for fast, isolated, shared-connection tests
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


from app.config.settings import settings
from app.database.migration import run_multi_tenancy_migration


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    os.environ["DEMO_MODE"] = "true"
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        # Create roles
        admin_role = Role(name="ADMIN", description="Administrator")
        user_role = Role(name="USER", description="Standard User")
        db.add_all([admin_role, user_role])
        db.commit()

        # Create users
        admin_user = User(
            id="test-admin-uuid",
            email="admin@test.local",
            hashed_password=hash_password("Password123!"),
            full_name="Admin Tester",
            role_id=admin_role.id,
            is_active=True,
            status="ACTIVE",
        )
        finops_user = User(
            id="test-user-uuid",
            email="user@test.local",
            hashed_password=hash_password("Password123!"),
            full_name="User Tester",
            role_id=user_role.id,
            is_active=True,
            status="ACTIVE",
        )
        db.add_all([admin_user, finops_user])
        db.commit()

        # Run multi-tenancy migration to create default-org and assign users
        run_multi_tenancy_migration(db, engine=test_engine)

        # Seed costs
        mock_provider = MockAWSProvider()
        cost_service = CostService(mock_provider)
        today = date.today()
        cost_service.sync_costs(db, start_date=today - timedelta(days=14), end_date=today)

        # Seed optimization recommendations
        opt_engine = OptimizationEngine(mock_provider)
        opt_engine.run_all(db)

    finally:
        db.close()

    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers():
    token = create_access_token(subject="test-admin-uuid", role="ADMIN")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers():
    token = create_access_token(subject="test-user-uuid", role="USER")
    return {"Authorization": f"Bearer {token}"}
