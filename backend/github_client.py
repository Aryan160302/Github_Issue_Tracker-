import re
from typing import Tuple

import requests

from .models import IssueRaw


class GitHubError(Exception):
    """Custom exception just so we can distinguish GitHub errors easily."""
    pass


def parse_repo_url(repo_url: str) -> Tuple[str, str]:
    """Parse a GitHub repo URL and return (owner, repo_name)."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        raise ValueError(f"Could not parse GitHub repo URL: {repo_url}")

    owner = match.group(1)
    repo = match.group(2)

    if repo.endswith(".git"):
        repo = repo[:-4]

    return owner, repo


def _build_headers(github_token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ollama-github-issue-assistant"
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def fetch_issue_and_comments(
    repo_url: str,
    issue_number: int,
    github_token: str | None = None,
) -> IssueRaw:
    """Fetch the issue title/body and comments from the GitHub API."""

    owner, repo = parse_repo_url(repo_url)
    base_url = "https://api.github.com"

    issue_url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}"
    headers = _build_headers(github_token)

    issue_resp = requests.get(issue_url, headers=headers, timeout=15)
    if issue_resp.status_code == 404:
        raise GitHubError("Issue or repository not found. Double-check the URL and issue number.")
    if issue_resp.status_code >= 400:
        raise GitHubError(f"GitHub API error (issue): {issue_resp.status_code} - {issue_resp.text}")

    issue_data = issue_resp.json()
    title = issue_data.get("title") or "(no title)"
    body = issue_data.get("body") or ""

    comments_url = issue_data.get("comments_url")
    comments: list[str] = []

    if comments_url:
        comments_resp = requests.get(comments_url, headers=headers, timeout=15)
        if comments_resp.status_code >= 400:
            raise GitHubError(f"GitHub API error (comments): {comments_resp.status_code} - {comments_resp.text}")

        comments_data = comments_resp.json()
        for c in comments_data:
            text = c.get("body") or ""
            if text.strip():
                comments.append(text.strip())

    MAX_TEXT_CHARS = 6000

    def _truncate(text: str) -> str:
        if len(text) <= MAX_TEXT_CHARS:
            return text
        return text[:MAX_TEXT_CHARS] + "\n\n[... truncated for analysis ...]"

    body = _truncate(body)
    comments = [_truncate(c) for c in comments]

    return IssueRaw(title=title, body=body, comments=comments)
