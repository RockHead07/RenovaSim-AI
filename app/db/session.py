# ---------------------------------------------------------------------------
# db/session.py
# Database engine and session factory.
# Import `get_session` as a FastAPI dependency in routes.
# ---------------------------------------------------------------------------

from sqlmodel import SQLModel, Session, create_engine
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,        # logs SQL queries in debug mode
    connect_args={"check_same_thread": False},  # required for SQLite
)


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency — yields a DB session per request."""
    with Session(engine) as session:
        yield session