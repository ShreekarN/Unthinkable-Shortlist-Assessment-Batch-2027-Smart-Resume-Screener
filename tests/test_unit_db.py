from app import db


def testCreateAndGetJob(testDbPath):
    job = db.createJob("Engineer", "Build APIs with Python")
    saved = db.getJob(job["id"])
    assert saved is not None
    assert saved["title"] == "Engineer"
    assert saved["description"] == "Build APIs with Python"


def testCreateCandidateAndShortlist(testDbPath):
    job = db.createJob("Engineer", "Python and SQL")
    parsedData = {
        "name": "Jane Doe",
        "skills": ["Python"],
        "experience": ["2 years backend"],
        "education": ["B.Tech"],
        "match": {"strengths": ["Python"], "gaps": []},
    }
    candidateId = db.createCandidate(
        job["id"], "jane.pdf", "raw text", parsedData, 8.5, "Strong Python fit"
    )
    row = db.getCandidate(candidateId)
    assert row is not None
    assert row["score"] == 8.5

    shortlist = db.getShortlist(job["id"], 7)
    assert len(shortlist) == 1

    below = db.getShortlist(job["id"], 9)
    assert len(below) == 0


def testGetMissingJob(testDbPath):
    assert db.getJob(9999) is None
