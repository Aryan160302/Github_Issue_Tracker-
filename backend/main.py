import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .github_client import GitHubError, fetch_issue_and_comments
from .llm_client import LLMConfigError, analyze_issue_with_llm
from .models import (
    ErrorResponse,
    HealthResponse,
    IssueAnalysis,
    IssueRequest,
)


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # optional


app = FastAPI(
    title="Ollama GitHub Issue Assistant",
    description=(
        "Given a GitHub issue, fetch details via the GitHub API, "
        "run it through a local Ollama model, and return a structured summary."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
    "/api/analyze_issue",
    response_model=IssueAnalysis,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def analyze_issue(payload: IssueRequest) -> IssueAnalysis:
    try:
        issue_raw = fetch_issue_and_comments(
            repo_url=str(payload.repo_url),
            issue_number=payload.issue_number,
            github_token=GITHUB_TOKEN,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except GitHubError as ge:
        raise HTTPException(status_code=400, detail=str(ge))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error talking to GitHub: {e}")

    try:
        analysis = analyze_issue_with_llm(
            issue=issue_raw,
            ollama_base_url=OLLAMA_BASE_URL,
            ollama_model=OLLAMA_MODEL,
        )
        return analysis
    except LLMConfigError as le:
        raise HTTPException(status_code=500, detail=str(le))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while talking to Ollama: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
