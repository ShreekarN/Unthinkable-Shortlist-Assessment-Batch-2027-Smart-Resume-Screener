import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile

from app import auth, db, groqclient, jobtemplates, parser
from app.config import shortlistMinScore
from app.models import (
    CandidateOut,
    JobCreate,
    JobOut,
    JobRoleOut,
    JobTemplateOut,
    LoginRequest,
    ParsedResumeItem,
    ShortlistItem,
    UploadResult,
    UserOut,
)

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


def buildParsedItem(row):
    parsed = json.loads(row["parsedJson"])
    return ParsedResumeItem(
        id=row["id"],
        name=parsed.get("name", "Unknown"),
        fileName=row["fileName"],
        score=row["score"],
        justification=row["justification"],
        skills=parsed.get("skills", []),
        experience=parsed.get("experience", []),
        education=parsed.get("education", []),
        shortlisted=row["score"] >= shortlistMinScore,
        createdAt=row["createdAt"],
    )


@router.post("/auth/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response):
    user = db.getUserByEmail(payload.email)
    if not user or not auth.verifyPassword(payload.password, user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth.createSession(user["id"])
    response.set_cookie(
        key=auth.cookieName,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=auth.sessionHours * 3600,
    )
    return UserOut(id=user["id"], email=user["email"])


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(auth.cookieName)
    auth.clearSession(token)
    response.delete_cookie(auth.cookieName)
    return {"message": "Logged out"}


@router.get("/auth/me", response_model=UserOut)
def currentUser(user=Depends(auth.requireUser)):
    return UserOut(id=user["id"], email=user["email"])


@router.get("/job-roles", response_model=list[JobRoleOut])
def listJobRoles(user=Depends(auth.requireUser)):
    return [JobRoleOut(**role) for role in jobtemplates.getRoleOptions()]


@router.get("/job-templates/{roleKey}", response_model=JobTemplateOut)
def getJobTemplate(roleKey: str, user=Depends(auth.requireUser)):
    template = jobtemplates.getDefaultJob(roleKey)
    if not template:
        raise HTTPException(status_code=404, detail="No default template for this role")
    return JobTemplateOut(**template)


@router.post("/jobs", response_model=JobOut)
def createJob(payload: JobCreate, user=Depends(auth.requireUser)):
    job = db.createJob(payload.title.strip(), payload.description.strip())
    return JobOut(**job)


@router.post("/resumes", response_model=UploadResult)
async def uploadResume(
    jobId: int = Form(...),
    file: UploadFile = File(...),
    user=Depends(auth.requireUser),
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
def getShortlist(jobId: int, user=Depends(auth.requireUser)):
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


@router.get("/jobs/{jobId}/parsed", response_model=list[ParsedResumeItem])
def getParsedResumes(jobId: int, user=Depends(auth.requireUser)):
    job = db.getJob(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    rows = db.getAllCandidates(jobId)
    return [buildParsedItem(row) for row in rows]


@router.get("/candidates/{candidateId}", response_model=CandidateOut)
def getCandidate(candidateId: int, user=Depends(auth.requireUser)):
    row = db.getCandidate(candidateId)
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return buildCandidate(row)
