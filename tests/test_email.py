import pytest
from unittest.mock import MagicMock
from datetime import datetime


# -----------------------------------
# 🧪 SEND EMAIL - SUCESSO
# -----------------------------------
def test_send_email_success(client, mock_publish):

    response = client.post(
        "/v2/send-email",
        json={
            "from_email": "teste@teste.com",
            "to_email": "destino@teste.com",
            "subject": "Teste",
            "message": "Olá mundo",
            "password": "123",
            "template": "default",
            "logo": None
        },
        headers={"Authorization": "TEST_TOKEN"}
    )

    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert data["status"] == "queued"


# -----------------------------------
# 🧪 SEND EMAIL - FALHA RABBIT
# -----------------------------------
def test_send_email_fail(client, monkeypatch):

    async def fail_publish(*args, **kwargs):
        return False, 3

    monkeypatch.setattr(
        "core.retry_rabbitmq.publish_with_retry",
        fail_publish
    )

    response = client.post(
        "/v2/send-email",
        json={
            "from_email": "teste@teste.com",
            "to_email": "destino@teste.com",
            "subject": "Erro",
            "message": "Falha",
            "password": "123",
            "template": "default",
            "logo": None
        },
        headers={"Authorization": "TEST_TOKEN"}
    )

    assert response.status_code == 500
    assert response.json()["status"] == "failed"


# -----------------------------------
# 🧪 UPDATE STATUS - SUCESSO
# -----------------------------------
def test_update_status_success(client, monkeypatch):

    fake_email = MagicMock()
    fake_email.id = "123"
    fake_email.status = "queued"
    fake_email.created_at = datetime.now()

    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = fake_email

    fake_db = MagicMock()
    fake_db.query.return_value = fake_query

    def override_db():
        yield fake_db

    monkeypatch.setattr("db.session.get_db", override_db)

    response = client.get(
        "/v2/update-status/123?Status=visualized&Token=TEST",
    )

    assert response.status_code == 200
    assert fake_email.status == "visualized"


# -----------------------------------
# 🧪 UPDATE STATUS - NÃO ENCONTRADO
# -----------------------------------
def test_update_status_not_found(client, monkeypatch):

    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = None

    fake_db = MagicMock()
    fake_db.query.return_value = fake_query

    def override_db():
        yield fake_db

    monkeypatch.setattr("db.session.get_db", override_db)

    response = client.get(
        "/v2/update-status/999?Status=visualized&Token=TEST",
    )

    assert response.status_code == 404


# -----------------------------------
# 🧪 EMAIL STATUS - BANCO
# -----------------------------------
def test_email_status_success(client, monkeypatch):

    fake_email = MagicMock()
    fake_email.id = "123"
    fake_email.status = "sent"
    fake_email.from_email = "a@a.com"
    fake_email.to_email = "b@b.com"
    fake_email.template = "default"
    fake_email.logo = None
    fake_email.subject = "Teste"
    fake_email.message = "Mensagem"
    fake_email.error_message = None
    fake_email.visualized_at = None
    fake_email.sent_at = None

    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = fake_email

    fake_db = MagicMock()
    fake_db.query.return_value = fake_query

    def override_db():
        yield fake_db

    monkeypatch.setattr("db.session.get_db", override_db)

    response = client.get(
        "/v2/email-status/123",
        headers={"Authorization": "TEST_TOKEN"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == "123"


# -----------------------------------
# 🧪 EMAIL STATUS - CACHE
# -----------------------------------
def test_email_status_cache(client, fake_redis):

    fake_redis.store["email_status:123"] = """
    {
        "id": "123",
        "status": "sent",
        "from_email": "a@a.com",
        "to_email": "b@b.com",
        "subject": "Teste",
        "message": "Mensagem"
    }
    """

    response = client.get(
        "/v2/email-status/123",
        headers={"Authorization": "TEST_TOKEN"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == "123"


# -----------------------------------
# 🧪 LISTAR EMAILS
# -----------------------------------
def test_get_emails(client, monkeypatch):

    fake_email = MagicMock()
    fake_email.id = "123"
    fake_email.status = "sent"
    fake_email.from_email = "a@a.com"
    fake_email.to_email = "b@b.com"
    fake_email.template = "default"
    fake_email.logo = None
    fake_email.subject = "Teste"
    fake_email.message = "Mensagem"
    fake_email.error_message = None
    fake_email.visualized_at = None
    fake_email.sent_at = None

    fake_query = MagicMock()
    fake_query.filter.return_value.all.return_value = [fake_email]

    fake_db = MagicMock()
    fake_db.query.return_value = fake_query

    def override_db():
        yield fake_db

    monkeypatch.setattr("db.session.get_db", override_db)

    response = client.get(
        "/v2/emails?From=a@a.com",
        headers={"Authorization": "TEST_TOKEN"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1