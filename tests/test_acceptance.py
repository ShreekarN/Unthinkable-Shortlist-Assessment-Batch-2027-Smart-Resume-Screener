import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.acceptance
def testFullFlowWithRealPdfs(testDbPath, sampleJob, pdfFiles, hasGroqKey):
    if not hasGroqKey:
        pytest.skip("GROQAPIKEY not configured in .env")

    if not pdfFiles:
        pytest.skip("No PDF files found in assessment folder")

    login = client.post(
        "/api/auth/login",
        json={"email": "abc@gmail.com", "password": "abc123"},
    )
    assert login.status_code == 200

    jobResponse = client.post("/api/jobs", json=sampleJob)
    assert jobResponse.status_code == 200
    jobId = jobResponse.json()["id"]

    uploaded = []
    for pdfPath in pdfFiles:
        with pdfPath.open("rb") as handle:
            response = client.post(
                "/api/resumes",
                data={"jobId": str(jobId)},
                files={"file": (pdfPath.name, handle, "application/pdf")},
            )

        assert response.status_code == 200, (
            f"Upload failed for {pdfPath.name}: {response.text}"
        )
        data = response.json()
        assert 1 <= data["score"] <= 10
        assert data["name"]
        uploaded.append(data)

    shortlist = client.get(f"/api/jobs/{jobId}/shortlist").json()
    parsed = client.get(f"/api/jobs/{jobId}/parsed").json()
    highScores = [item for item in uploaded if item["score"] >= sampleJob["minScore"]]
    assert len(shortlist) == len(highScores)
    assert len(parsed) == len(uploaded)

    for item in uploaded:
        detail = client.get(f"/api/candidates/{item['id']}").json()
        assert detail["justification"]
        assert isinstance(detail["skills"], list)
        assert isinstance(detail["experience"], list)
        assert isinstance(detail["education"], list)
