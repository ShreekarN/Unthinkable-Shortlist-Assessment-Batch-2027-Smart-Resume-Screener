from pydantic import BaseModel, Field

# Response/request shapes for auth, jobs, candidates, archive, and shortlist.


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=3)


class UserOut(BaseModel):
    id: int
    email: str


class JobRoleOut(BaseModel):
    key: str
    label: str


class JobTemplateOut(BaseModel):
    title: str
    description: str


class JobCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    minScore: float = Field(default=7, ge=1, le=10)


class JobOut(BaseModel):
    id: int
    title: str
    description: str
    createdAt: str
    minScore: float


class CandidateOut(BaseModel):
    # Full assessment payload for detail panel and /candidate page.
    id: int
    jobId: int
    fileName: str
    name: str
    score: float
    justification: str
    strengths: list[str]
    gaps: list[str]
    evidencePhrases: list[str]
    skills: list[str]
    experience: list[str]
    education: list[str]
    createdAt: str
    archived: bool = False
    hasRawText: bool = True
    rawText: str = ""


class ArchiveResult(BaseModel):
    id: int
    archived: bool
    archivedAt: str
    message: str


class ShortlistItem(BaseModel):
    id: int
    name: str
    fileName: str
    score: float
    justification: str
    strengths: list[str]


class ParsedResumeItem(BaseModel):
    id: int
    name: str
    fileName: str
    score: float
    justification: str
    skills: list[str]
    experience: list[str]
    education: list[str]
    shortlisted: bool
    archived: bool
    hasRawText: bool
    createdAt: str


class UploadResult(BaseModel):
    id: int
    name: str
    score: float
    shortlisted: bool
    message: str
