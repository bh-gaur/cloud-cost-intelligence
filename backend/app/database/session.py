"""
Database Engine & Session Management
Supports PostgreSQL for production and SQLite for local development and unit tests.
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings

from pathlib import Path
import logging

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )
    if not db_url.startswith("sqlite"):
        with engine.connect():
            pass
except Exception as e:
    backend_dir = Path(__file__).resolve().parent.parent.parent
    fallback_url = f"sqlite:///{backend_dir / 'cloud_cost.db'}"
    logger.warning("Database connection to '%s' failed (%s). Falling back to SQLite at '%s'.", db_url, e, fallback_url)
    db_url = fallback_url
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=settings.DEBUG,
    )

if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

