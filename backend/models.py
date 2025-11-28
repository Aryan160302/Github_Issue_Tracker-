from typing import Literal, List

from pydantic import BaseModel, HttpUrl, Field


class IssueRequest(BaseModel):
    repo_url: HttpUrl
    issue_number: int = Field(..., ge=1, description="GitHub issue number (starts from 1)")


class IssueRaw(BaseModel):
    title: str
    body: str = ""
    comments: List[str] = []


class IssueAnalysis(BaseModel):
    summary: str
    type: Literal["bug", "feature_request", "documentation", "question", "other"]
    priority_score: str
    suggested_labels: List[str]
    potential_impact: str


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
