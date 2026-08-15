from fastapi.testclient import TestClient

from api.fastapi_app import create_app
from api.fastapi_auth import create_token
from api.fastapi_deps import get_db
from fasthtml.common import to_xml
from pages.legal import account_deletion_page, privacy_page


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeDB:
    def __init__(self, first_row=None):
        self.first_row = first_row
        self.statements = []
        self.commits = 0

    def execute(self, statement, params=None):
        self.statements.append((str(statement), params or {}))
        row = self.first_row
        self.first_row = None
        return _Result(row)

    def commit(self):
        self.commits += 1


def _client_with_db(db):
    app = create_app()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def test_delete_account_removes_associated_data():
    db = _FakeDB(first_row=(123,))
    client = _client_with_db(db)
    token = create_token(123, "reviewer@example.com")

    response = client.delete(
        "/account",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    sql = "\n".join(statement for statement, _ in db.statements)
    assert "DELETE FROM kanvas.ai_content_reports" in sql
    assert "DELETE FROM kanvas.chat_messages" in sql
    assert "DELETE FROM kanvas.chat_sessions" in sql
    assert "DELETE FROM kanvas.user_profiles" in sql
    assert "DELETE FROM kanvas.chat_users" in sql
    assert db.commits == 1


def test_ai_content_report_is_recorded_without_login():
    db = _FakeDB()
    client = _client_with_db(db)

    response = client.post(
        "/reports/ai-content",
        json={
            "reason": "Misleading or inaccurate",
            "response_content": "Reported answer",
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "INSERT INTO kanvas.ai_content_reports" in db.statements[0][0]
    assert db.statements[0][1]["content"] == "Reported answer"
    assert db.commits == 1


def test_public_legal_pages_name_the_app_and_deletion_paths():
    privacy = to_xml(privacy_page())
    deletion = to_xml(account_deletion_page())

    assert "Predictive Labs Ltd" in privacy
    assert "Kanvas" in privacy
    assert "/account-deletion" in privacy
    assert "Profile &amp; Preferences" in deletion
    assert "info@predictivelabs.ai" in deletion
