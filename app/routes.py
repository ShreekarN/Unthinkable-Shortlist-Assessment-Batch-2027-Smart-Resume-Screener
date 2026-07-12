import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app import db, groqclient, parser
from app.config import shortlistMinScore
from app.models import CandidateOut, JobCreate, JobOut, ShortlistItem, UploadResult

router = APIRouter()


def buildCandidate(row):
    parsed = json.loads(row["parsedJson"])
    matchData = parsed.get("match", {})
    return CandidateOut(
        id=row["id"],
        jobId=row["jobId"],
        fileName=row["fileName"],
        name=parsed.get("name", "Unknown"),
        score=row["score"],
        justification=row["justification"],
        strengths=matchData.get("strengths", []),
        gaps=matchData.get("gaps", []),
        skills=parsed.get("skills", []),
        experience=parsed.get("experience", []),
        education=parsed.get("education", []),
        createdAt=row["createdAt"],
    )


@router.post("/jobs", response_model=JobOut)
def createJob(payload: JobCreate):
    job = db.createJob(payload.title.strip(), payload.description.strip())
    return JobOut(**job)


@router.post("/resumes", response_model=UploadResult)
async def uploadResume(
    jobId: int = Form(...),
    file: UploadFile = File(...),
):
    job = db.getJob(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    fileName = file.filename or "resume.txt"
    fileBytes = await file.read()
    if not fileBytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        rawText = parser.extractText(fileName, fileBytes)
        parsedResume = groqclient.extractResume(rawText)
        matchData = groqclient.matchResume(parsedResume, job["description"])
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    parsedResume["match"] = matchData
    score = matchData["score"]
    justification = matchData["justification"]
    candidateId = db.createCandidate(
        jobId, fileName, rawText, parsedResume, score, justification
    )

    shortlisted = score >= shortlistMinScore
    message = "Added to shortlist" if shortlisted else "Processed but below shortlist threshold"

    return UploadResult(
        id=candidateId,
        name=parsedResume.get("name", "Unknown"),
        score=score,
        shortlisted=shortlisted,
        message=message,
    )


@router.get("/jobs/{jobId}/shortlist", response_model=list[ShortlistItem])
def getShortlist(jobId: int):
    job = db.getJob(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    rows = db.getShortlist(jobId, shortlistMinScore)
    items = []
    for row in rows:
        parsed = json.loads(row["parsedJson"])
        matchData = parsed.get("match", {})
        items.append(
            ShortlistItem(
                id=row["id"],
                name=parsed.get("name", "Unknown"),
                fileName=row["fileName"],
                score=row["score"],
                justification=row["justification"],
                strengths=matchData.get("strengths", []),
            )
        )
    return items


@router.get("/candidates/{candidateId}", response_model=CandidateOut)
def getCandidate(candidateId: int):
    row = db.getCandidate(candidateId)
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return buildCandidate(row)
