import pytest
import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

load_dotenv(".env.test")

os.environ["ENV"] = "test"

from api import main 

@pytest.fixture
def client():
    return TestClient(main)


@pytest.fixture
def fake_redis():
    class FakeRedis:
        def __init__(self):
            self.store = {}

        async def get(self, key):
            return self.store.get(key)

        async def set(self, key, value, ex=None):
            self.store[key] = value

        async def delete(self, key):
            self.store.pop(key, None)

    return FakeRedis()


@pytest.fixture(autouse=True)
def override_redis(fake_redis, monkeypatch):
    
    main.state.redis = fake_redis


@pytest.fixture
def fake_db():
    db = MagicMock()
    return db


@pytest.fixture(autouse=True)
def override_db(fake_db, monkeypatch):

    def fake_get_db():
        yield fake_db

    monkeypatch.setattr("db.session.get_db", fake_get_db)


@pytest.fixture
def mock_publish(monkeypatch):

    async def fake_publish(*args, **kwargs):
        return True, 1  # sucesso, 1 tentativa

    monkeypatch.setattr(
        "core.retry_rabbitmq.publish_with_retry",
        fake_publish
    )


@pytest.fixture(autouse=True)
def bypass_auth(monkeypatch):

    def fake_validate_token():
        return True

    monkeypatch.setattr(
        "auth.auth.validade_token",
        fake_validate_token
    )
    

@pytest.fixture
def fake_email():
    return {
        "id": "123",
        "from_email": "a@a.com",
        "to_email": "b@b.com",
        "subject": "teste",
        "message": "msg",
        "status": "queued"
    }