from pydantic import BaseModel, Field


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


class JobOut(BaseModel):
    id: int
    title: str
    description: str
    createdAt: str


class CandidateOut(BaseModel):
    id: int
    jobId: int
    fileName: str
    name: str
    score: float
    justification: str
    strengths: list[str]
    gaps: list[str]
    skills: list[str]
    experience: list[str]
    education: list[str]
    createdAt: str


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
    createdAt: str


class UploadResult(BaseModel):
    id: int
    name: str
    score: float
    shortlisted: bool
    message: str
