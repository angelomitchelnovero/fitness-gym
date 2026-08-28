"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.db.session import get_db
from app.main import app


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
