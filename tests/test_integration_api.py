from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def testHomePageLoads():
    response = client.get("/")
    assert response.status_code == 200
    assert "Smart Resume Screener" in response.text


def testLoginPageLoads():
    response = client.get("/login")
    assert response.status_code == 200
    assert "Sign In" in response.text


def testCreateJob(testDbPath, sampleJob):
    client.post("/api/auth/login", json={"email": "abc@gmail.com", "password": "abc123"})
    response = client.post("/api/jobs", json=sampleJob)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] > 0
    assert data["title"] == sampleJob["title"]


def testUploadResumeWithMockedGroq(testDbPath, sampleJob):
    client.post("/api/auth/login", json={"email": "abc@gmail.com", "password": "abc123"})
    jobResponse = client.post("/api/jobs", json=sampleJob)
    jobId = jobResponse.json()["id"]

    parsedResume = {
        "name": "Test User",
        "skills": ["Python", "FastAPI"],
        "experience": ["3 years backend"],
        "education": ["B.Sc Computer Science"],
    }
    matchData = {
        "score": 8.0,
        "justification": "Strong Python and API experience.",
        "strengths": ["Python", "FastAPI"],
        "gaps": ["Limited SQL depth"],
    }

    resumeText = (
        "Test User\nPython developer with FastAPI experience.\n"
        "Education: B.Sc Computer Science"
    )

    from unittest.mock import patch

    with patch("app.routes.parser.extractText", return_value=resumeText), patch(
        "app.routes.groqclient.extractResume", return_value=parsedResume
    ), patch("app.routes.groqclient.matchResume", return_value=matchData):
        response = client.post(
            "/api/resumes",
            data={"jobId": str(jobId)},
            files={"file": ("resume.txt", resumeText, "text/plain")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 8.0
    assert data["shortlisted"] is True

    shortlist = client.get(f"/api/jobs/{jobId}/shortlist")
    assert shortlist.status_code == 200
    items = shortlist.json()
    assert len(items) == 1

    parsed = client.get(f"/api/jobs/{jobId}/parsed")
    assert parsed.status_code == 200
    assert len(parsed.json()) == 1

    detail = client.get(f"/api/candidates/{data['id']}")
    assert detail.status_code == 200
    detailData = detail.json()
    assert detailData["skills"] == ["Python", "FastAPI"]


def testUploadResumeJobNotFound(testDbPath):
    client.post("/api/auth/login", json={"email": "abc@gmail.com", "password": "abc123"})
    response = client.post(
        "/api/resumes",
        data={"jobId": "999"},
        files={"file": ("resume.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 404


def testUploadEmptyFile(testDbPath, sampleJob):
    client.post("/api/auth/login", json={"email": "abc@gmail.com", "password": "abc123"})
    jobId = client.post("/api/jobs", json=sampleJob).json()["id"]
    response = client.post(
        "/api/resumes",
        data={"jobId": str(jobId)},
        files={"file": ("resume.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


def testGetCandidateNotFound(testDbPath):
    client.post("/api/auth/login", json={"email": "abc@gmail.com", "password": "abc123"})
    response = client.get("/api/candidates/9999")
    assert response.status_code == 404


def testProtectedRouteRequiresLogin(testDbPath):
    freshClient = TestClient(app)
    response = freshClient.get("/api/job-roles")
    assert response.status_code == 401
