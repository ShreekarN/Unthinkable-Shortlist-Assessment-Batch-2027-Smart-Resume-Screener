from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def testLoginSuccess(testDbPath):
    response = client.post(
        "/api/auth/login",
        json={"email": "abc@gmail.com", "password": "abc123"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "abc@gmail.com"


def testLoginFailure(testDbPath):
    response = client.post(
        "/api/auth/login",
        json={"email": "abc@gmail.com", "password": "wrong"},
    )
    assert response.status_code == 401


def testJobRolesAndTemplate(testDbPath):
    client.post("/api/auth/login", json={"email": "abc@gmail.com", "password": "abc123"})
    roles = client.get("/api/job-roles")
    assert roles.status_code == 200
    assert any(role["key"] == "backend" for role in roles.json())

    template = client.get("/api/job-templates/backend")
    assert template.status_code == 200
    body = template.json()
    assert "Core Skills:" in body["description"]
    assert "Keywords:" in body["description"]
    assert "Impact Metrics:" in body["description"]
