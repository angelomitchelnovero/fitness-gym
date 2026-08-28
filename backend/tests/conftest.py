"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """FastAPI test client."""
    with TestClient(app) as c:
        yield c
