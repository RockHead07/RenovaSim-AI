import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from app.main import app
from app.db.session import get_session
from app.db.seeder import seed_job_types


@pytest.fixture(scope="session")
def client() -> TestClient:
    # Use an in-memory SQLite DB for tests — isolated, never touches renovasim.db
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    def get_test_session():
        with Session(test_engine) as session:
            seed_job_types(session)
            yield session

    app.dependency_overrides[get_session] = get_test_session

    return TestClient(app)