"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
from collections.abc import Generator

# Ensure JWT_SECRET is set before any app module imports settings.
os.environ.setdefault("JWT_SECRET", "test-secret-not-used-for-real-auth")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def db_session() -> Generator:
    """In-memory SQLite session, schema created fresh per test."""
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    sess = session_factory()
    try:
        yield sess
    finally:
        sess.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session) -> Generator[TestClient, None, None]:
    """FastAPI test client wired to the in-memory DB."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
