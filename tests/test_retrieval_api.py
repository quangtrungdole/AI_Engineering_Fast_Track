from fastapi.testclient import TestClient

from app.main import app
from app.mock_jira import app as mock_jira_app

client = TestClient(app)
mock_jira_client = TestClient(mock_jira_app)


def test_search_is_served_by_main_app(monkeypatch):
    monkeypatch.setattr("app.retrieval_api.search", lambda query, project_id, top_k: [])

    response = client.post(
        "/search",
        headers={"X-Allowed-Project": "ALPHA"},
        json={"query": "release date", "project_id": "ALPHA"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_search_rejects_unauthorized_project():
    response = client.post(
        "/search",
        headers={"X-Allowed-Project": "BETA"},
        json={"query": "release date", "project_id": "ALPHA"},
    )

    assert response.status_code == 403


def test_search_is_not_served_by_mock_jira():
    response = mock_jira_client.post(
        "/search",
        headers={"X-Allowed-Project": "ALPHA"},
        json={"query": "release date", "project_id": "ALPHA"},
    )

    assert response.status_code == 404