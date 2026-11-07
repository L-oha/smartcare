import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.database import get_session
from app.main import app


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def client(test_db):
    def session_override():
        with Session(test_db) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    try:
        # Skip startup seeding and use only the test's in-memory data.
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_session)
