# ---------------------------------------------------------------------------
# conftest.py
# Shared test fixtures — pytest picks this up automatically.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Single TestClient instance shared across all tests in the session.
    No real server is started — requests are handled in-process.
    """
    return TestClient(app)