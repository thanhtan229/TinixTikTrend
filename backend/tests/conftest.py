import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.fixtures.sample_data import seed_sample_data


# Shared in-memory test engine with StaticPool
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def isolate_local_tiktok_session(tmp_path, monkeypatch):
    # Unit/integration fixtures must never load a user's signed-in session.
    from app.collectors.tiktok_shop import session
    monkeypatch.setattr(session, 'SESSION_FILE', tmp_path / 'test-session.json')


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_sample_data(db)
    db.close()
    
    def override_get_db():
        db_session = TestingSessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)
