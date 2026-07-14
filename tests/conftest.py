import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.database import Base
from app.main import app
from fastapi.testclient import TestClient
from app.api.deps import get_current_user, get_db
import uuid


class FakeUser:
    def __init__(self, email="alhaji@gmail.com"):
        self.id = uuid.uuid4().hex
        self.email = email
        self.is_verified = True
        self.is_active = True

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def engine(postgres_container: PostgresContainer):
    engine = create_engine(postgres_container.get_connection_url())

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def authenticated_client(client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser()
    return client
