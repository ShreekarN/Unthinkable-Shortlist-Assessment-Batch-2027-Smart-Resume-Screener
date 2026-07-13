from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def testHomeRedirectsWhenLoggedOut():
    freshClient = TestClient(app)
    response = freshClient.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def testHomePageLoadsWhenLoggedIn(testDbPath):
    client.post("/api/auth/login", json={"email": "abc@gmail.com", "password": "abc123"})
    response = client.get("/")
    assert response.status_code == 200
    assert "Smart Resume Screener" in response.text


def testLoginPageLoads():
    freshClient = TestClient(app)
    response = freshClient.get("/login")
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
        "evidencePhrases": ["FastAPI experience"],
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
    assert detailData["rawText"] == resumeText
    assert detailData["evidencePhrases"] == ["FastAPI experience"]


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


def testArchiveCandidateKeepsAssessment(testDbPath, sampleJob):
    client.post("/api/auth/login", json={"email": "abc@gmail.com", "password": "abc123"})
    jobId = client.post("/api/jobs", json=sampleJob).json()["id"]

    from unittest.mock import patch

    parsedResume = {
        "name": "Archive User",
        "skills": ["Python"],
        "experience": ["2 years"],
        "education": ["B.Tech"],
    }
    matchData = {
        "score": 6.0,
        "justification": "Moderate fit for the role.",
        "strengths": ["Python"],
        "gaps": ["FastAPI"],
    }

    with patch("app.routes.parser.extractText", return_value="raw resume text"), patch(
        "app.routes.groqclient.extractResume", return_value=parsedResume
    ), patch("app.routes.groqclient.matchResume", return_value=matchData):
        upload = client.post(
            "/api/resumes",
            data={"jobId": str(jobId)},
            files={"file": ("resume.txt", b"raw resume text", "text/plain")},
        )

    candidateId = upload.json()["id"]
    archive = client.post(f"/api/candidates/{candidateId}/archive")
    assert archive.status_code == 200

    detail = client.get(f"/api/candidates/{candidateId}").json()
    assert detail["archived"] is True
    assert detail["hasRawText"] is False
    assert detail["score"] == 6.0
    assert detail["justification"] == "Moderate fit for the role."


def testCustomThresholdShortlist(testDbPath):
    client.post("/api/auth/login", json={"email": "abc@gmail.com", "password": "abc123"})
    job = {
        "title": "QA Engineer",
        "description": "Testing role with selenium and API testing.",
        "minScore": 6,
    }
    jobId = client.post("/api/jobs", json=job).json()["id"]

    from unittest.mock import patch

    parsedResume = {
        "name": "Threshold User",
        "skills": ["Python"],
        "experience": ["2 years"],
        "education": ["B.Tech"],
    }
    matchData = {
        "score": 6.5,
        "justification": "Moderate fit.",
        "strengths": ["Python"],
        "gaps": ["Selenium"],
    }

    with patch("app.routes.parser.extractText", return_value="resume text"), patch(
        "app.routes.groqclient.extractResume", return_value=parsedResume
    ), patch("app.routes.groqclient.matchResume", return_value=matchData):
        upload = client.post(
            "/api/resumes",
            data={"jobId": str(jobId)},
            files={"file": ("resume.txt", b"resume text", "text/plain")},
        )

    assert upload.json()["shortlisted"] is True
    shortlist = client.get(f"/api/jobs/{jobId}/shortlist").json()
    assert len(shortlist) == 1


def testProtectedRouteRequiresLogin(testDbPath):
    freshClient = TestClient(app)
    response = freshClient.get("/api/job-roles")
    assert response.status_code == 401
