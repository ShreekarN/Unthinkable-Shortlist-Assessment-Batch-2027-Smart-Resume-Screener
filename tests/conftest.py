import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, db
from app.main import app

pdfDir = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def testDbPath(monkeypatch):
    tempFile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tempFile.close()
    monkeypatch.setattr(config, "dbPath", Path(tempFile.name))
    db.initDb()
    yield Path(tempFile.name)
    if os.path.exists(tempFile.name):
        os.remove(tempFile.name)


@pytest.fixture
def authClient(client, testDbPath):
    response = client.post(
        "/api/auth/login",
        json={"email": "abc@gmail.com", "password": "abc123"},
    )
    assert response.status_code == 200
    return client


@pytest.fixture
def sampleJob():
    return {
        "title": "Backend Developer",
        "description": (
            "Core Skills:\nPython, FastAPI, REST APIs, SQL\n\n"
            "Keywords:\nresume parsing, LLM integration\n\n"
            "Impact Metrics:\nscoring accuracy, reduced screening time"
        ),
        "minScore": 7,
    }


@pytest.fixture
def pdfFiles():
    names = ["N.pdf", "O.pdf", "P.pdf", "Q.pdf", "mynewcv (1).pdf"]
    files = []
    for name in names:
        path = pdfDir / name
        if path.exists():
            files.append(path)
    return files


@pytest.fixture
def hasGroqKey():
    return bool(config.groqApiKey and config.groqApiKey != "your_key_here")
